# B3 Phase-43 run-method notes (full post-change measurement session fingerprints)

> This file records the harness fingerprint of every Phase-43 measurement session, the installed
> cache parity record, the snapshot record and the retune record, and nothing else. It supersedes
> nothing. `RUN-METHOD-NOTES-v2.10.md`, `RUN-METHOD-NOTES-phase40.md` and
> `RUN-METHOD-NOTES-phase41.md`, and every fingerprint in them, are untouched: Phase-38 scoring walks
> `RUN-METHOD-NOTES-v2.10.md` for its own session binding (`SCORING-v2.10.md` §9), the Phase-40 and
> Phase-41 spot-check runs bind to their own notes files, so a Phase-43 session block in any of them
> would enter an evidence chain it has no part in. A reader looking for the provenance of a Phase-43
> run (`runs-v2.10-phase43/`) comes here.

Corollary the binding depends on: BECAUSE this file is mutable, nothing downstream trusts its live
content. Every check reads this file's COMMITTED blob (`git show HEAD:<this file>`) and binds each
run to the commit that introduced its session block, never to the working file.

## Harness pin

`pin-claude-code` and `pin-codex` are carried byte-for-byte from `RUN-METHOD-NOTES-phase41.md`
(`2.1.281 (Claude Code)` is the value `SUPERSESSIONS-v2.10.md` entry 006 accepted on 2026-09-24, a
named confound against the 2.1.261 Phase-38 baseline). `pin-model` is tightened to the EXACT
`fable 5.1`: ledger entry 003 in `SUPERSESSIONS-v2.10.md` (D-03b) applies to Phase 43, so a
`fable 5.2` session, or a bare `fable 5`, is harness drift and is never aggregated. Two pins are new
in Phase 43: `pin-codex-companion` (the `codex@openai-codex` plugin version from
`~/.claude/plugins/installed_plugins.json`) and `pin-context-window` (D-03: the 1M window, a
disclosed harness difference from the 200k Phase-38 baseline). These five lines are the only
column-0 pin lines in this file; every prose mention of a pin label is backticked so an anchored
grep for each label returns exactly one value.

pin-claude-code: 2.1.281 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: fable 5.1
pin-codex-companion: 1.0.4
pin-context-window: 1M

A pin line may be corrected ONLY while this file holds zero session blocks and
`runs-v2.10-phase43/` holds zero run commits. After that, drift makes the affected runs
unscoreable. Any correction is recorded as a new `SUPERSESSIONS-v2.10.md` entry, never silently.

## Run method

One disclosure line (not a pin; the fingerprint's `driver:` field binds each session to it):

run-method: assistant-driven via tmux (D-13, owner decision 2026-09-30, Phase-40/41 precedent) — each measured session is a separate claude process in its own tmux session; the driver sends only the launch line, /clear, CLEARED, /vibe-check:deep-review, Step A 4, Step C 3, /exit and never feeds findings

`CLEARED` is the typed attestation the `pre` block reads on its own stdin (the driver feeds it to
the block, not to the measured session). The `post` block asserts, from each run's local
transcript, that every record classified as driver input by its record provenance belongs to the
fixed set above (`driver contamination: none`).

## Seal verifier

The current seal-verifier pin and the count-==-2 consumer rule live in `SUPERSESSIONS-v2.10.md`
entry 004. They are not restated here: a second copy is a second thing to drift.

## The per-session block (what the `fingerprint` block appends here)

The executable block is `fingerprint` in `RUN-PHASE43-v2.10.md` (the one file the measurement is
driven from). This section is its contract, so a reader can check a session block against the
rule without reading bash.

**When.** Once per Claude Code launch, after the session is open and before its first run. A
relaunch (a new diff, a new sitting, a crash) is a new session and gets a new block.

**Header.** The singular timestamped form, `## Harness fingerprint — <YYYY-MM-DDTHH:MM:SS±ZZZZ>`.
The plural section header at the end of this file falls outside that anchored pattern, so a file
with zero sessions can never satisfy a binding lookup.

**Fields, one per line, in this order:**

| field | value | source |
|---|---|---|
| `claude-code:` | exact `claude --version` output | CLI probe; a failure STOPS, no fallback |
| `model:` | the model name exactly as the session UI shows it, with a trailing ` (1M context)` stripped by the block before the grammar check | typed transcription |
| `context-window:` | must be exactly `1M` | typed transcription from `/model` or `/context` |
| `codex:` | exact `codex --version` output, full x.y.z | CLI probe |
| `codex-companion:` | the `codex@openai-codex` version | `~/.claude/plugins/installed_plugins.json` |
| `autoupdate:` | the `claude doctor` Auto-updates line | CLI probe |
| `batch-sha:` | the snapshot's `snapshot_commit` | the verified snapshot's `MANIFEST.json` |
| `snapshot-root:` | the snapshot worktree path | the active-window record, re-verified |
| `plugin-root:` | the `--plugin-dir` launch argument | the LAST line of `batchsnap.py verify` |
| `driver:` | `assistant-tmux` or `owner`; Phase 43 expects `assistant-tmux` | typed transcription |
| `session:` | the label of the window (`first` or `retune`) and the diff the session was launched for | the active-window record + the block argument |

`batch-sha:`, `snapshot-root:` and `plugin-root:` bind every Phase-43 session to the exact frozen
plugin tree it ran against. There is no `cache-root:` field: a measured run never resolves from the
installed cache (the `post` block voids a transcript naming it); the cache is held at content
parity with the snapshot only so that nothing the harness loads by side path differs (§Cache
parity).

**Assertions before anything is appended (each one STOPS on failure):**

1. `model:` (after the ` (1M context)` strip) full-line matches
   `^(claude[- ])?(fable)[- ]5\.1$` case-insensitively and carries no placeholder text. A bare
   `fable 5` or any other minor STOPS.
2. `context-window:` is exactly `1M`. If the launch's `[1m]` model suffix was rejected, select the
   1M variant in `/model` and re-run the block.
3. `claude-code:`, `codex:` and `codex-companion:` byte-equal their pin lines, parsed from THIS
   file's committed blob.
4. Cross-session constancy: the normalized `model:` value byte-equals every prior `model:` line in
   THIS file's committed blob. Earlier notes files are never read for this check.
5. `driver:` matches `assistant-tmux|owner`.

**Commit.** Pathspec-scoped to THIS file only (`git commit --only -- <this file>`); the scope assert
inspects the commit resolved from that pathspec, never `HEAD`, and requires it to touch this file
and nothing else.

**Run binding.** Each run's `pre` block writes `session.txt` (the latest session ID in this file's
committed blob + the sha of the commit that introduced it) BEFORE the review is triggered, and
asserts that session's `batch-sha:` and `plugin-root:` equal the active window's. The `post` block
asserts the introducing commit's time and the `clear.txt` time both precede the review's recorded
pass timestamp.

## Cache parity

`resync-cache` appends one line here per resync, in the form
`parity: <snapshot_commit> forward=<n>/<n> reverse=0 extra at <ISO time>`; `restore-cache` appends
`parity: restored released 2.9.0 at <ISO time>`. The `preflight` block requires the committed blob
to carry a `parity: <the active snapshot_commit>` line, and re-runs the same two-direction content
hash check itself; it never compares version strings.

parity: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536 forward=106/106 reverse=0 extra at 2026-09-30T21:26:45-0400

## Snapshot

One line per measurement snapshot built with `batchsnap.py build`, in the form
`snapshot: batch<N> <snapshot_commit> <snapshot_root>`. The `preflight` block re-derives the
snapshot from its own `MANIFEST.json`; this line is the human-readable record of which commit was
measured.

snapshot: batch5 be6b0fcd9a4c2794dd3351ea054a65f3ab91e536 /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c

## Retune

43-06 appends exactly one line: `retune: not used …` or `retune: used …`.

## Harness fingerprints — Phase 43

## Harness fingerprint — 2026-09-30T21:27:39-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first triggarr-secret-in-logs

## Harness fingerprint — 2026-09-30T22:12:29-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first triggarr-autoescape

## Harness fingerprint — 2026-09-30T22:49:28-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first third-organic-should-catch

## Harness fingerprint — 2026-09-30T23:18:05-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first should-quiet-1

## Harness fingerprint — 2026-09-30T23:44:27-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first should-quiet-2

## Harness fingerprint — 2026-10-01T00:05:02-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first should-quiet-3

## Harness fingerprint — 2026-10-01T00:32:00-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first triggarr-session-rotation

## Harness fingerprint — 2026-10-01T01:06:01-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first triggarr-settings-form-split

## Harness fingerprint — 2026-10-01T01:42:04-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first should-quiet-4

## Harness fingerprint — 2026-10-01T02:15:14-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
context-window: 1M
codex: codex-cli 0.153.4
codex-companion: 1.0.4
autoupdate: Auto-updates: disabled (set by env: DISABLE_AUTOUPDATER)
batch-sha: be6b0fcd9a4c2794dd3351ea054a65f3ab91e536
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch5-be6b0fcd9a4c/plugins/vibe-check
driver: assistant-tmux
session: first should-quiet-5
