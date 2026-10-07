# B3 Phase-49 run-method notes (v2.11 release-candidate measurement session fingerprints)

> This file records the harness fingerprint of every Phase-49 measurement session, the installed
> cache parity record, the snapshot record and the retune record, and nothing else. It supersedes
> nothing. `RUN-METHOD-NOTES-phase43.md` and every earlier notes file, and every fingerprint in
> them, are untouched: the Phase-43 runs bind to their own notes file, so a Phase-49 session block
> in any of them would enter an evidence chain it has no part in. A reader looking for the
> provenance of a Phase-49 run (`runs-v2.11-phase49/`) comes here. Dress-rehearsal records never
> go in this file: the only rehearsal line here is the single `rehearsal-snapshot:` line under
> §Snapshot; every other rehearsal record (parity, fingerprint, session) goes to
> `runs-v2.11-phase49/rehearsal/REHEARSAL-NOTES.md`.

Corollary the binding depends on: BECAUSE this file is mutable, nothing downstream trusts its live
content. Every check reads this file's COMMITTED blob (`git show HEAD:<this file>`) and binds each
run to the commit that introduced its session block, never to the working file.

## Harness pin

The five pins are carried byte-for-byte from `RUN-METHOD-NOTES-phase43.md`, so the v2.11 numbers
are measured on the same harness as the Phase-43 numbers they are compared against. Each value
was re-verified live on 2026-10-06 before this file was committed (`claude --version`,
`codex --version`, and the `codex@openai-codex` version in `~/.claude/plugins/installed_plugins.json`);
`pin-model` is the exact `fable 5.1` the measured sessions are launched with
(`--model 'claude-fable-5-1[1m]'`), and `pin-context-window` is the 1M window. These five lines are
the only column-0 pin lines in this file; every prose mention of a pin label is backticked so an
anchored grep for each label returns exactly one value.

pin-claude-code: 2.1.281 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: fable 5.1
pin-codex-companion: 1.0.4
pin-context-window: 1M

A pin line may be corrected ONLY while this file holds zero session blocks and
`runs-v2.11-phase49/first/` holds zero run commits. After that, drift makes the affected runs
unscoreable. Any correction is recorded as a new `SUPERSESSIONS-v2.10.md` entry, never silently.

## Run method

One disclosure line (not a pin; the fingerprint's `driver:` field binds each session to it):

run-method: assistant-driven via tmux (separate claude process per session; fixed keystroke set only)

The fixed keystroke set is: the launch line, `/clear`, `/vibe-check:deep-review`, on the "Pass N"
fix-loop card the option labelled exactly `Stop here…`, on the "Stop here" card the option
labelled exactly `Abandon` (both selected BY LABEL, never by position), and `/exit`. `CLEARED` is
the typed attestation the `pre` block reads on its own stdin (the driver feeds it to the block,
not to the measured session). The `post` block asserts, from each run's local transcript, that
every record classified as driver input by its record provenance belongs to that set
(`driver contamination: none`).

## Seal verifier

The current seal-verifier pin and the count-==-2 consumer rule live in `SUPERSESSIONS-v2.10.md`
entry 004. They are not restated here: a second copy is a second thing to drift.

## The per-session block (what the `fingerprint` block appends here)

The executable block is `fingerprint` in `RUN-PHASE49-v2.11.md`. Its contract is the Phase-43
contract (`RUN-METHOD-NOTES-phase43.md` §"The per-session block") unchanged, with three
differences: the pins are parsed from THIS file's committed blob, the cross-session `model:`
constancy check reads only THIS file, and the `session:` field carries `first` or `retune`. Under
`LABEL=rehearsal` the block writes to `runs-v2.11-phase49/rehearsal/REHEARSAL-NOTES.md` instead.

**Header.** `## Harness fingerprint — <YYYY-MM-DDTHH:MM:SS±ZZZZ>`, appended at the end of this
file under §Sessions. Fields in order: `claude-code:`, `model:`, `context-window:`, `codex:`,
`codex-companion:`, `autoupdate:`, `batch-sha:`, `snapshot-root:`, `plugin-root:`, `driver:`
(`assistant-tmux` expected), `session:`.

## Cache parity

`resync-cache` appends one line here per resync, in the form
`parity: <40-hex snapshot sha> forward=<n>/<n> reverse=0 extra at <ISO>`; `restore-cache` appends
`parity: restored released 2.10.0 at <ISO>`. The `preflight` block requires the committed blob to
carry a `parity: <the active snapshot_commit>` line and re-runs the same two-direction content
hash check itself; it never compares version strings. 49-05 and 49-06 gate (2)(v) parse both line
forms.

parity: e6eafbd3b8c4242064997f82fad5edd058d65a1c forward=134/134 reverse=0 extra at 2026-10-06T22:06:46-0400

## Snapshot

One line per measurement snapshot built with `batchsnap.py build`, in the form
`snapshot: batch<N> <40-hex> <root>` (batch 7 = the first pass, S; batch 8 = the retune, S2). The
dress rehearsal records its own build once, in the form `rehearsal-snapshot: batch7 <40-hex> <root>`,
which no measured label ever reads. The `preflight` block re-derives the snapshot from its own
`MANIFEST.json`; this line is the human-readable record of which commit was measured.

rehearsal-snapshot: batch7 9e095611c719e18cc8cdaa3af4c73e1f9f00ed50 /Users/julianamacbook/.vibe-check-snapshots/batch7-9e095611c719
snapshot: batch7 e6eafbd3b8c4242064997f82fad5edd058d65a1c /Users/julianamacbook/.vibe-check-snapshots/batch7-e6eafbd3b8c4

## Retune

49-07 appends exactly one `retune:` line per phase, in one of these forms:

- `retune: not used (first-pass verdict PASS at <sha>, <YYYY-MM-DD>)`
- `retune: declined by owner (…)`
- `retune: used (R=<40-hex>, S2=<40-hex>, fix-class: <X>, failed diffs: <list>; re-run: all 12 diffs x3 on S2)`

With a used retune it also appends `fix-class: PROMPT|CODE — <target>`. The release decision is
recorded as `ship-decision: <ship-as-measured|ship-without-fix|no-ship> (owner, <timestamp>, verdict of record <PASS|MISS> <X>/18 <Y>/15)`,
and a reverted fix as `ship-revert: <40-hex revert sha> (revert of R=<40-hex>)`. 49-08's release
gate and 49-09's pre-flight parse these COMMITTED lines, never a SUMMARY.

## Sessions
