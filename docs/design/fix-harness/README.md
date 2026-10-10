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

Options: `--plugin-source` (default `plugins/vibe-check`; must be under
`plugins/`), `--command review|deep-review` (default `review`).

Each run:

1. creates a workspace under the temp dir and snapshots the plugin into it;
2. builds the copy, seeds the pass-1 state and records ledger snapshot 0;
3. plants the three sentinels (preservation only; `sentinels.json` goes to
   `--out`, never into the copy);
4. builds the session settings and runs the preflight, which needs a passed
   probe record for this SDK version and policy fingerprint;
5. drives the session. The plugin's state is read before every card and
   after every turn. In default-diff mode, a loop that ends on "No changes to
   review." (or a sibling one-liner) gets `/vibe-check:review --finalize`
   from the harness, recorded as an owner command (D-24). Clean-tree runs
   check `git status` outside `.turingmind/` before Close out or that
   `--finalize` (FLOW-04);
6. writes `obligations.json`, judges the committed HEAD and writes
   `run.json`.

The workspace (copy + snapshot) is kept so it can be inspected; its paths
are in `run.json`. `check --run <dir>` re-validates the record and, while the
copy still exists, re-runs the verdict with the saved obligation ledger.

`replay --case … --mode … --kind … --messages <jsonl> --out <dir>` feeds
recorded cards (`{"card": …}`), tool calls (`{"tool": …, "input": …}`) and
turn ends (`{"turn_end": …}`) through the same core and permission dispatch
without the SDK, and writes `replay.json`.

Exit codes: `0` COMPLETE (probe passed, replay clean, check clean), `1`
FAILED, `2` usage, preflight or driver error. No record is written on `2`.

### Sandbox probe

```
$PY probe-sandbox --out <scratch>/probe
```

The probe gates every launch. Rerun it after an SDK upgrade or any change to
the containment policy; the preflight says when the record no longer matches.
It writes `fixtures/probe/sandbox-probe.json` only when every required check
passes. On failure it prints each failed check and, for every file-tool
step, the verbatim tool result and how it was classified.

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
