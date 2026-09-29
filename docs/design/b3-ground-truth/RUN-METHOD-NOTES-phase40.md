# B3 Phase-40 run-method notes (spot-check session fingerprints)

> This file records the harness fingerprint of every Phase-40 spot-check session, and nothing else.
> It supersedes nothing. `RUN-METHOD-NOTES-v2.10.md` and every fingerprint in it are untouched:
> Phase-38 scoring walks that file for its own session binding (`SCORING-v2.10.md` §9), so a
> Phase-40 session block there would enter an evidence chain it has no part in. A reader looking
> for the provenance of the sealed baseline sessions goes to `RUN-METHOD-NOTES-v2.10.md`; a reader
> looking for the provenance of a Phase-40 spot-check run goes here.

Corollary the binding depends on: BECAUSE this file is mutable, nothing downstream trusts its live
content. Every check reads this file's COMMITTED blob (`git show HEAD:<this file>`) and binds each
run to the commit that introduced its session block, never to the working file.

## Harness pin

Carried from the Phase-38 pin (byte-for-byte, except `pin-claude-code`, corrected 2026-09-24 per
`SUPERSESSIONS-v2.10.md` entry 006) so that harness drift between the sealed baseline and a
Phase-40 spot-check is detected rather than silently absorbed. These three lines are the only
column-0 pin lines in this file; every prose mention of a pin label is backticked so an anchored
grep for each label returns exactly one value.

pin-claude-code: 2.1.281 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: fable 5

The `pin-model` grammar here stays the Phase-38 family+generation form
`(fable|opus|sonnet|haiku) 5(\.[0-9]+)?`. The exact-`fable 5.1` tightening belongs to Phase 43
(ledger entry 003 in `SUPERSESSIONS-v2.10.md`) and is NOT applied to the Phase-40 spot-checks.

A pin line may be corrected ONLY while this file holds zero session blocks and
`runs-v2.10-phase40/` holds zero run commits. After that, drift makes the affected runs
unscoreable. Any correction is recorded as a new `SUPERSESSIONS-v2.10.md` entry, never silently.

**Known at authoring (2026-09-24):** `claude --version` on the owner's machine reported
`2.1.281 (Claude Code)`, not the pinned `2.1.261 (Claude Code)`; `codex --version` matched its pin.
As written, the STEP 0.25 fingerprint block therefore STOPS at the first batch until this is
resolved: either run under the pinned CLI, or record a Phase-40 pin correction as a ledger entry
while zero Phase-40 sessions exist (and accept that CLI version as a named confound against the
baseline). That is a decision for the owner, taken before batch 1, not something the checklist
works around.

**Resolved 2026-09-24 (before batch 1):** the owner chose to accept `2.1.281 (Claude Code)` and record
it. The correction is `SUPERSESSIONS-v2.10.md` entry 006; the Claude Code version is a named confound
against the 2.1.261 baseline for every Phase-40 spot-check. `pin-codex` and `pin-model` are unchanged.

## Seal verifier

The current seal-verifier pin and the count-==-2 consumer rule live in `SUPERSESSIONS-v2.10.md`
entry 004. They are not restated here: a second copy is a second thing to drift.

## The per-session block (what STEP 0.25 appends here)

The executable block is STEP 0.25 of `SPOT-CHECK-v2.10-phase40.md` (the one file the owner runs
blocks from). This section is its contract, so a reader can check a session block against the rule
without reading bash.

**When.** Once per Claude Code launch, after the session is open and before its first run. A
relaunch is a new session and gets a new block.

**Header.** The singular timestamped form, `## Harness fingerprint — <YYYY-MM-DDTHH:MM:SS±ZZZZ>`.
The plural section header at the end of this file falls outside that anchored pattern, so a file
with zero sessions can never satisfy a binding lookup.

**Fields, one per line, in this order:**

| field | value | source |
|---|---|---|
| `claude-code:` | exact `claude --version` output | CLI probe; a failure STOPS, no fallback |
| `model:` | the model name exactly as the session UI shows it | typed transcription |
| `codex:` | exact `codex --version` output, full x.y.z | CLI probe |
| `batch:` | `batch1`, `batch2`, `batch3` or `final` | the pre-flight active-batch record |
| `batch-sha:` | the snapshot's `snapshot_commit` | the verified snapshot's `MANIFEST.json` |
| `snapshot-root:` | the snapshot worktree path | the active-batch record, re-verified |
| `plugin-root:` | the `--plugin-dir` launch argument | the LAST line of `batchsnap.py verify` |

`batch-sha:`, `snapshot-root:` and `plugin-root:` bind every Phase-40 session to the exact frozen
plugin tree it ran against. The Phase-38 `cache-root:` field is DROPPED: the helper-resolution rule
it recorded was removed by TRUST-01, and a Phase-40 run never resolves from the installed cache.

**Assertions before anything is appended (each one STOPS on failure):**

1. `model:` full-line matches `^(claude[- ])?(fable|opus|sonnet|haiku)[- ]5(\.[0-9]+)?(-[0-9]{8})?$`
   and carries no placeholder text.
2. `claude-code:` and `codex:` byte-equal the two pin lines above, parsed from THIS file's
   committed blob.
3. The normalized model's family+generation EXACTLY equals the `pin-model` value.
4. Cross-session constancy: the normalized `model:` value byte-equals every prior `model:` line in
   THIS file's committed blob. The Phase-38 notes are never read for this check.

**Commit.** Pathspec-scoped to THIS file only (`git commit --only -- <this file>`); the scope assert
inspects the commit resolved from that pathspec, never `HEAD`, and requires it to touch this file
and nothing else.

**Run binding.** Each run's pre-run block writes `session.txt` (the latest session ID in this
file's committed blob + the sha of the commit that introduced it) BEFORE the review is triggered,
and asserts that session's `batch-sha:` and `plugin-root:` equal the active batch's. The post-run
block asserts the introducing commit's time and the `clear.txt` time both precede the review's
recorded pass timestamp.

## Harness fingerprints — Phase 40

## Harness fingerprint — 2026-09-27T14:13:59-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch1
batch-sha: 39e11a7eef89fcd8a4e6b3b08319a172ba8b7069
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89/plugins/vibe-check

## Harness fingerprint — 2026-09-27T14:15:13-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch1
batch-sha: 39e11a7eef89fcd8a4e6b3b08319a172ba8b7069
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89/plugins/vibe-check

## Harness fingerprint — 2026-09-27T14:19:47-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch1
batch-sha: 39e11a7eef89fcd8a4e6b3b08319a172ba8b7069
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89/plugins/vibe-check

## Harness fingerprint — 2026-09-27T14:20:01-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch1
batch-sha: 39e11a7eef89fcd8a4e6b3b08319a172ba8b7069
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch1-39e11a7eef89/plugins/vibe-check

## Harness fingerprint — 2026-09-28T19:34:00-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch2
batch-sha: 1dd609ba1582d6702c9591153411dc6278fa727a
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch2-1dd609ba1582
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch2-1dd609ba1582/plugins/vibe-check

## Harness fingerprint — 2026-09-28T19:34:14-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch2
batch-sha: 1dd609ba1582d6702c9591153411dc6278fa727a
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch2-1dd609ba1582
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch2-1dd609ba1582/plugins/vibe-check

## Harness fingerprint — 2026-09-28T21:00:01-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch3
batch-sha: e79bff32c01feeaff1f02a2ab76375aaaa518786
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch3-e79bff32c01f
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch3-e79bff32c01f/plugins/vibe-check

## Harness fingerprint — 2026-09-28T21:00:15-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: batch3
batch-sha: e79bff32c01feeaff1f02a2ab76375aaaa518786
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch3-e79bff32c01f
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch3-e79bff32c01f/plugins/vibe-check

## Harness fingerprint — 2026-09-28T21:20:52-0400
claude-code: 2.1.281 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
batch: final
batch-sha: e79bff32c01feeaff1f02a2ab76375aaaa518786
snapshot-root: /Users/julianamacbook/.vibe-check-snapshots/batch3-e79bff32c01f
plugin-root: /Users/julianamacbook/.vibe-check-snapshots/batch3-e79bff32c01f/plugins/vibe-check
