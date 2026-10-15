# Accepted-fix harness

A scripted end-to-end check of vibe-check's accepted-fix flow. Each run starts
on a disposable git copy of a small synthetic case whose defect, fix and tests
are known, launches the local plugin against it, answers its cards from the
seeded finding's identity only, and judges the result from the copy's commits,
state and files.

This directory lives outside `plugins/` on purpose: nothing here ships with
the plugin or enters its manifest.

## Layout

```
fix-harness/
├── README.md
├── requirements.txt      # Agent SDK pin for the harness venv only
├── fixtures/<case-id>/   # synthetic cases: base/, defect/, gsd/, recipe.json
├── keys/<case-id>.json   # answer-key-shaped record (never copied into a run)
└── tools/                # harness modules + their unit tests
```

A case's `recipe.json` names the fixed and untouched files, the test command,
a harness-only defect check, the defect hunk's line span in the defect
version, the three sentinel sites and the GSD phase id.

## Install

The Agent SDK lives in a harness-only venv (gitignored). It is never
installed into the plugin or into system Python:

```
cd docs/design/fix-harness
uv venv .venv --python 3.14
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -c "import importlib.metadata as m; print(m.version('claude-agent-sdk'))"   # 0.2.165
```

Installed 2026-10-10 with CPython 3.14.5: `claude-agent-sdk==0.2.165`, which
bundles Claude Code CLI 2.1.294. Only `tools/harness_driver_sdk.py` imports the
SDK, and only inside the function that launches a session, so every other
module and every unit test runs on the system `python3` without it.

Unit tests are stdlib-only and run with bare `pytest -q` from `tools/`.

## Run

Launch from the repository root with the harness venv's Python and
`CLAUDECODE` unset. One command per run; `--out` must be a new or empty dir
(it is read-denied to the session):

```
H=docs/design/fix-harness
PY="env -u CLAUDECODE $H/.venv/bin/python $H/tools/fixharness.py"

$PY run --case py-clamp-01 --mode default --kind preservation --out <dir>/P-D   # /vibe-check:review
$PY run --case py-clamp-01 --mode gsd     --kind preservation --out <dir>/P-G   # /vibe-check:review 52-harness-case
$PY run --case py-clamp-01 --mode default --kind clean        --out <dir>/C-D   # /vibe-check:review --finalize (entry: finalize)
$PY run --case py-clamp-01 --mode gsd     --kind clean        --out <dir>/C-G   # /vibe-check:review 52-harness-case
```

Options: `--candidate <rev>` (the commit the plugin snapshot is taken from;
default the active freeze manifest's `candidate_sha`), `--manifest <path>`
(default the highest-numbered `docs/design/freeze-v2.12/FREEZE-MANIFEST-<N>.json`),
`--command review|deep-review` (default `review`). There is no option to skip
or override the identity check.

Each run:

1. creates a workspace under the temp dir and materializes
   `plugins/vibe-check` from the candidate commit's tree into it (never from
   the working tree, so untracked or uncommitted files are not measured);
2. builds the copy, seeds the pass-1 state and records ledger snapshot 0;
3. plants the three sentinels (preservation only; `sentinels.json` goes to
   `--out`, never into the copy);
4. builds the session settings and runs the preflight, which needs a passed
   probe record for this SDK version and policy fingerprint, and an exact
   match from the shared freeze identity check (`freeze_check.verify`,
   runner `fix-harness`) on the snapshot, the session's environment and the
   manifest's `launch_model`. Any difference, or no manifest at all, stops
   the run with exit 2. The session is then launched with that model and
   that environment; an init-reported model that differs fails the run;
5. drives the session. The plugin's state is read before every card and
   after every turn. In default-diff mode, a loop that ends on "No changes to
   review." (or a sibling one-liner) gets `/vibe-check:review --finalize`
   from the harness, recorded as an owner command (D-24). Clean-tree runs
   check `git status` outside `.turingmind/` before Close out or that
   `--finalize` (FLOW-04);
6. writes `obligations.json`, judges the committed HEAD and writes
   `run.json`, which carries the verified `manifest_id`, `check_digest` and
   `candidate_sha`.

The workspace (copy + snapshot) is kept so it can be inspected; its paths
are in `run.json`. `check --run <dir>` re-validates the record and, while the
copy still exists, re-runs the verdict with the saved obligation ledger.

`replay --case … --mode … --kind … --messages <jsonl> --out <dir>` feeds
recorded cards (`{"card": …}`), tool calls (`{"tool": …, "input": …}`) and
turn ends (`{"turn_end": …}`) through the same core and permission dispatch
without the SDK, and writes `replay.json`.

Exit codes: `0` COMPLETE (probe passed, replay clean, check clean), `1`
FAILED, `2` usage, preflight or driver error. No record is written on `2`.

### State location (format-53)

The harness seeds and judges the review state at the path the plugin's
`statepath.resolve_current` names: `.turingmind/state/format-53/<key>`.
The legacy location (`statepath.resolve`) is never a fallback:

- seeding refuses when a legacy-location state already exists for the key
  (`legacy-location state present at <path> — the harness never seeds over an old-format file`),
  so the plugin cannot migrate a stale file into the run;
- the verdict reads only archives under `.turingmind/state/format-53/`. With
  no archive there, a legacy-location state or archive adds the FAILED reason
  `legacy-location state found at <paths> — the plugin wrote the old format; not accepted`
  beside `state not archived`. A legacy file next to a
  format-53 archive is ignored.

Condition 3 (Finalize) fails a claimed successful close-out on:

- undecided Needs-verification items:
  `undecided Needs-verification at finalize: N`
  (they are also counted in `outstanding findings at finalize: N`);
- any obligation that left the state without a decision:
  `obligation dropped without decision: <hash7>`
  (a seeded finding also adds `seeded finding not verified resolved: <hash7>`).

A defer or dismiss decision with a non-blank reason is kept as disposition
`decided` and is not a problem; one without a reason fails as
`obligation decision without reason: <hash7>`. Needs-verification rows reach Finalize
through the real cards and are deferred by number with the harness reason,
never fixed in place of the seeded finding.

### Sandbox probe

```
$PY probe-sandbox --out <scratch>/probe
```

The probe gates every launch. Rerun it after an SDK upgrade or any change to
the containment policy; the preflight says when the record no longer matches.
It writes `fixtures/probe/sandbox-probe.json` only when every required check
passes. On failure it prints each failed check and, for every file-tool
step, the verbatim tool result and how it was classified.

**Result on this host (2026-10-10):** PASSED, 37 of 37 checks, with
claude-agent-sdk 0.2.165 / Claude Code 2.1.294 and policy fingerprint
`2590e9f6…` (re-recorded in 52-11 after the private-temp policy change). All four Bash escapes (read the protected canary, read the key,
write into the checkout, write into the snapshot) exited 1 with `Operation
not permitted`. All four file-tool escapes were blocked by the deny rules
before reaching the harness. The two permitted operations of each channel
worked. Evidence per step, and the probe's history, are in
`fixtures/probe/README.md`.

## A1 — plugin identity

Resolved 2026-10-10, live. With `setting_sources=[]` and
`plugins=[{"type": "local", "path": <snapshot>}]`, the init message listed
exactly one `vibe-check`, at the snapshot path
(`source: vibe-check@inline`), in both the probe session and the smoke
session. The installed `vibe-check@thejuran` cache copy did not appear. The
same list also carries Claude Code's builtin plugins (`cc-plugin-agents-md`,
`cc-plugin-telemetry`, and in the smoke session `cc-plugin-plugin-authoring`,
all with `path: builtin`). The driver tolerates those and requires exactly
one `vibe-check` at the snapshot path. No option adjustment was needed.

## A2 — launching from inside Claude Code

Resolved 2026-10-10, live. Both the probe and the smoke session were
launched from a Bash call inside a Claude Code session, with
`env -u CLAUDECODE` on the command line. The driver also drops `CLAUDECODE`
from the session env, and the SDK drops it from the inherited set. Both
sessions started, and no plain terminal was needed.

## Smoke session (2026-10-10)

`run --case py-clamp-01 --mode default --kind preservation` ran twice. The
first run surfaced the account-connector leak (see Containment), so it was
rerun once the policy was fixed and the probe re-recorded. Both runs ended
the same way: **FAILED**, with a validated `run.json`. Making runs complete
is plan 52-11's job. The rerun:

- passed the preflight. The init message listed one `vibe-check`, at the
  snapshot path, and no MCP server;
- answered two real fix-loop cards (`Apply all & rerun`), both captured.
  The first is in `fixtures/replay/fix-loop-card.json`;
- the fix landed as one commit, `fix(review-pass-2): …`, touching only
  `src/clamp.py`;
- 0 protected-path denials, 0 backstop denials;
- the obligation ledger holds 5 snapshots (seed, card, card, turn_end,
  final), every one with a full HEAD sha; 2 hashes tracked, none open and
  retained;
- 513 s of automated execution time; owner-waiting time not measured.

Verdict reasons: `.turingmind/REVIEW.md missing`, `state not archived`,
`turn ended on unrecognised text`. On pass 3 the plugin could not close the
seeded finding:

1. The finding is attributed to the `logic` agent, which `/vibe-check:review`
   does not dispatch, so no recheck can resolve it.
2. The fix agent's "obsolete" verdict is not recorded while the fixed file
   differs from HEAD, and here it differs because of the planted fixed-file
   sentinel.

The session then stopped and listed options in prose. The harness counted
that as a would-be owner question and failed the run, as designed. Plan
52-11 fixed both: the key now names `bugs`, a reviewer `/vibe-check:review`
always dispatches, so the normal recheck closes the finding, and the
obsolete-verdict rule is correct as designed (see
`runs/phase52/RUNS.md`, "52-10 carry-overs").

## Status (Phase 52)

The four matrix cells ran live on `py-clamp-01` through the plugin in this
working tree, all on one plugin build, and all four are **COMPLETE**:

| run | mode | kind | entry | verdict |
|-----|------|------|-------|---------|
| P-D | default | preservation | review | COMPLETE |
| P-G | gsd | preservation | review | COMPLETE |
| C-D | default | clean | finalize | COMPLETE |
| C-G | gsd | clean | review | COMPLETE |

Records, transcripts, counts, timing, failed attempts and the defects the
runs exposed (four plugin, two harness, each fixed with a test) are in
`runs/phase52/RUNS.md`. `tools/test_harness_isolation.py` locks every
`runs/phase52/*/run.json` to a valid COMPLETE record. It also locks this
directory against any reference to the benchmark or holdout inputs. The
harness was proven on synthetic fixtures only.

## Phase 55 usage

Phase 55 reuses the same CLI (`fixharness.py run`, one command per run) for
the mandatory measured runs. The cases for those runs come from the answer
keys, supplied at Phase 55 under its release-by-role rules. They are not
part of this phase, and nothing here reads them.

## Phase 52 gate

Both suites were run on the merged tree before any of the four live runs, at
commit `c28f3e8` (2026-10-10):

- plugin suite (bare `pytest -q` in `plugins/vibe-check/scripts`):
  `2487 passed, 3469 subtests passed`
- harness suite (bare `pytest -q` in `docs/design/fix-harness/tools`):
  `374 passed, 113 subtests passed`

No integration fix was needed.

After the four live runs and their fixes, on the tree that carries the four
COMPLETE records (plan 52-11's final commit):

- plugin suite: `2502 passed, 3542 subtests passed`
- harness suite: `389 passed, 213 subtests passed`

Each run keeps its workspace (copy + snapshot) and its private temp root
(`/tmp/fh…`) for inspection. Neither lives in this checkout. Delete them by
hand when no longer needed.

## Isolation rules

- Cases are synthetic. Never build a case from the B3 benchmark diffs or the
  holdout set, and never read those inputs from harness code.
- Answer keys never enter the copy. The copy builder copies only a case's
  `base/` (and `gsd/` in GSD layout) plus the defect file; `keys/`,
  `recipe.json` and the defect check stay outside the run.
- After launch, every state change in the copy comes through the plugin. The
  harness seeds state and plants sentinels before launch and only reads the
  copy afterwards.

## Session isolation

- **Plugin under test:** each run snapshots `plugins/vibe-check` into a
  per-run workspace and loads that copy by local path
  (`plugins=[{"type": "local", "path": <snapshot>}]`). The driver asserts
  the init message lists exactly one `vibe-check`, at the snapshot path, so
  an installed cache copy can never be the build under test.
- **Settings:** `setting_sources=[]`, so no user, project or local settings
  file (and no `~/.claude/CLAUDE.md`) is loaded. The only settings are the
  containment policy, passed inline as the flag layer.
- **Environment:** the parent environment minus `CLAUDECODE`.
- **Memory:** every run's cwd is a fresh temp path, so the per-project
  auto-memory directory is fresh too.

## Containment

The disposable copy restricts nothing on its own: an absolute-path read of
`keys/` or a write into this checkout would simply succeed. Every session
therefore runs under three layers (`tools/harness_sandbox.py`):

1. **OS sandbox (Seatbelt)** around Bash and everything it spawns. The
   checkout, the run's out dir, `keys/` and host credential files are
   read-denied, and the plugin snapshot is write-denied.
   `failIfUnavailable` and `allowUnsandboxedCommands: false` make a missing
   sandbox stop the session rather than run it unsandboxed.
2. **Permission deny rules** (`Read(//…/**)`, `Edit(//…/**)`,
   `NotebookEdit`) for the in-process file tools, which the OS sandbox does
   not wrap.
3. **Path backstop** in the driver's `can_use_tool`: every file-tool path
   must resolve inside the copy (or, read-only, the snapshot), both lexically
   and through symlinks. A protected path is denied and FAILS the run. A
   path elsewhere outside the copy is denied and counted in the record.

The copy and the snapshot live under the per-user temp dir, outside this
checkout: the checkout is denied with `//`-anchored rules that cannot be
carved open again for a subdirectory.

**Account MCP connectors are off.** `setting_sources=[]` does not stop
Claude Code from loading the owner's claude.ai account connectors (Gmail,
Drive, …). The first smoke session loaded seven of them, and a subagent called
one. MCP tools run inside the Claude Code process, outside Seatbelt. Every
session therefore sets `disableClaudeAiConnectors` in the policy, runs with
`ENABLE_CLAUDEAI_MCP_SERVERS=false` and `--strict-mcp-config` (no servers),
and refuses to continue if the init message lists any MCP server. The
backstop denies any `mcp__` tool call and fails the run.

**Private temp root.** Claude Code's own temp dir defaults to the per-uid
`/tmp/claude-<uid>`, which every Claude Code session of the same user shares,
and it auto-allows file tools there. Each run therefore creates a short 0700
temp root before launch and passes it as `CLAUDE_CODE_TMPDIR`, so the session's
temp files (and the sandbox's `$TMPDIR`) live under it. The shared
`/tmp/claude-<uid>` (both `/tmp` spellings) is read- and write-denied in
Seatbelt and in the permission rules, and the driver refuses a missing or
shared temp root. The probe does not attempt the shared dir; the deny is part
of the fingerprinted policy and locked by `settings_is_fail_closed`.

**What the backstop sees.** `can_use_tool` is reached only by calls that
would prompt. Claude Code auto-allows reads under the cwd, some in-copy
edits by subagents, and file-tool calls under its own (now per-run) temp
dir, so those never reach the backstop. Protected paths
are blocked for every agent by the deny rules, whether a call prompts or
not, and the probe proves that. `containment.denials` counts only the calls
the backstop saw.

The model API credentials are untouched. The Claude Code process uses them
outside the sandbox, as it always does; only the tools it runs are contained.

The live sandbox probe (`fixharness.py probe-sandbox`) proves on this host
that both escapes are blocked, through Bash and through the file tools, and
that the permitted operations still work. `run` refuses to launch without a
passed probe record matching the installed SDK version and the current
policy fingerprint.

## No harness writes after launch (D-21)

The harness writes into the copy only before launch: building it, seeding
the pass-1 state and planting sentinels. Once the session starts, every
state change comes through the plugin. The driver opens no file outside the
run's out dir and imports none of the modules that build, seed or plant. The
core's state observations, taken before every card and after every turn, are
plain reads.

## Timing labels

Each run record reports the automated execution time and the harness's own
answer time. Time spent waiting on the owner is not measured in a scripted run:
it is recorded as `null` with the note "not measured — scripted run, no human
in the loop", never as zero.
