# Phase-54 live-check notes — targeted live check — not release evidence

**Label: targeted live check — not release evidence.** Every number in this file comes from one
live run per signed-off development case on the final code candidate (D-27). Release measurement
is Phase 55 (the frozen candidate through B3 x3 and the sealed holdout x3). Nothing under
`runs-phase54-live/` is read by `score43.py aggregate`, `ledger` or the replay censuses.

Runbook: `docs/design/reachability-dev/RUN-PHASE54-live.md` (blocks run through the committed B3
runner layer `docs/design/b3-ground-truth/b3-runner-v2.12/`). Transcripts stay local (gitignored);
only `transcript.jsonl.sha256` is committed.

## Harness pins

pin-claude-code: 2.1.281 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: claude-fable-5-1[1m]

The pins equal the Phase-53 rehearsal (`NOTES-phase53-dev.md` `## Harness pins`). The model value
is the one the identity check compares with the manifest's B3 launch model
(`launch_model.b3.value` = `claude-fable-5-1[1m]` in the draft manifest). `claude --version` and
`codex --version` were checked live on 2026-10-15T22:08Z; the identity check compares the binaries
themselves, not only the version strings.

## Pre-registration — 2026-10-15T22:20Z (before the first run)

- **Candidate:** `302df48e1097212aa334a21c8f2683ed810eb496`, read from
  `docs/design/freeze-v2.12/evidence/CANDIDATE.json` (never `HEAD`).
- **Manifest:** the draft `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`,
  `manifest_id` `b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c`, used as
  `MANIFEST` for the whole sweep (the series file does not exist yet).
- **Disposable clones:** `~/.b3/phase54-clones/{roonseek,seedsyncarr,triggarr}`, cloned fresh from
  the owner's local repos at `main`, push URL disabled (`no-push-disposable-clone`), local exclude
  `.turingmind/` and `.planning/HANDOFF.json`. Environment folders built before the first run as in
  Phase-53 entry 3: triggarr `.venv` (Python 3.11) and roonseek `.venv` (Python 3.13) from the
  clone's committed `uv.lock` (`uv sync --frozen --all-extras --all-groups`); the triggarr package
  set equals the owner's; roonseek lacks the one package the owner installed outside the lock
  (`musicbrainzngs`), left uninstalled as in Phase 53; seedsyncarr `src/angular/node_modules` is a
  copy-on-write copy of the owner's. All three clones `git status` clean after provisioning. No
  block runs `checkout`, `switch`, `stash` or `revert` against the owner's repos.
- **Isolated runner:** `~/.b3/phase54-runner/plugin/vibe-check`, materialized from the candidate
  commit's git objects (`materialize` block). Only measured sessions load it (`--plugin-dir` +
  `--settings ~/.b3/phase54-runner/settings-measured.json`, which disables the installed
  `vibe-check@thejuran` for that session).
- **Owner cache untouched:** the installed `vibe-check@thejuran` cache is never resynced. Its
  fingerprint is recorded before and after the sweep under `## Cache`.
- **Auto-memory parked** for the three clone paths (`park-memory` block) before the first run and
  restored after the last (`restore-memory`).
- **One run per case** (`run-1`), in the Phase-53 final-sweep order: `reach-new-1`, `reach-new-2`,
  `reach-unchanged-1`, `reach-unchanged-2`, `triggarr-secret-in-logs`, `triggarr-autoescape`,
  `third-organic-should-catch`, `should-quiet-1`, `should-quiet-2`, `should-quiet-3`,
  `triggarr-session-rotation`, `triggarr-settings-form-split`, `should-quiet-4`, `should-quiet-5`,
  `should-quiet-6`, `should-quiet-7`. A crashed or refused run goes to `attempts/` (`fail`) and is
  redone with the next run number on the same candidate; a completed run is never rerun for a
  better outcome. No retune.
- **Keystrokes fixed:** launch (the `session` block via tmux), `/clear`, `/vibe-check:deep-review`,
  `Stop here…` then `Abandon` (by label), `/exit`. Driver: `run_case.sh`, assistant-driven via
  tmux, `--permission-mode manual`. An unexpected card, prompt or permission request = STOP.
- **Comparison:** each outcome against the Phase-53 signed-off final run
  (`NOTES-phase53-dev.md` `## Tally`); every changed outcome goes into the R4 before/after table.
  A lost catch is investigated, never rerun.

## Pre-registration — restart on candidate 24c0c00 — 2026-10-15T22:52Z (before the first run)

The 302df48 attempt above stopped at its first case (`## Deviations`, SWEEP STOPPED). Commit
24c0c00 fixed the cause (`.in_use/` session-marker directories are no longer hashed) and changed
covered freeze-kit files, so 54-10 selected a new candidate and regenerated the draft manifest.
This sweep starts over on that candidate. The 302df48 entries above stay as the record of the
first attempt; nothing from it counts here (it produced no run directory).

- **Candidate:** `24c0c00038f2d15af4b55f178ea44e680c1f2c58`, read from
  `docs/design/freeze-v2.12/evidence/CANDIDATE.json` (never `HEAD`). It equals the draft
  manifest's `candidate_sha`.
- **Manifest:** the regenerated draft at the same path,
  `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`, `manifest_id`
  `98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99`, used as `MANIFEST` for the
  whole sweep. Its B3 launch model is `claude-fable-5-1[1m]` (`models.launch_model.b3`), equal to
  `pin-model:` above, so the pins are unchanged (`claude --version` 2.1.281, `codex --version`
  0.153.4, checked live 2026-10-15T22:52Z).
- **Everything else as the first pre-registration:** the same three disposable clones (re-used;
  each on its start branch and `git status` clean at 22:52Z: roonseek `2370f0b`, seedsyncarr
  `3dc75c7`, triggarr `4a154be`), the isolated runner re-materialized from 24c0c00, memory parked
  again, owner cache untouched, one run per case in the same order, no retune, the same fixed
  keystrokes, the same comparison and lost-catch rule.
- **First live test of the `.in_use` fix:** the `pre` and `post` checks run while the measured
  session is alive. If either refuses again, the sweep stops with the exact difference list; no
  marker is deleted and nothing is patched.

## Candidate

candidate-guard (2026-10-15T22:08Z, before any block):

```text
CANDIDATE OK candidate=302df48e1097212aa334a21c8f2683ed810eb496 head=bd5884c3c6d6eba11678d4fd98dbda70cd184891 descendant_commits=4 (reporting-only)
```

`materialize 302df48e1097212aa334a21c8f2683ed810eb496`: runner copy
`~/.b3/phase54-runner/plugin/vibe-check` := `302df48e…:plugins/vibe-check` (git archive); runner
settings from the same commit (`<RUNNER>` -> `~/.b3/phase54-runner`). `identity` (all three clone
dirs, first attempt, no refusal):

```text
IDENTITY OK manifest_id=b6abbae38b9cf544df57e7ea201fadf66ec9a1643094974894a7abc7c595755c check_digest=3ce2bac84c3831cc74b538874ddaab0e7c96e539f3b37fb68f3a953c55650f5c candidate_sha=302df48e1097212aa334a21c8f2683ed810eb496
```

`park-memory`: none of the three fresh clone paths had auto-memory; park record
`~/.b3/automemory-parked-phase54-live-1792102177`.

### Restart on 24c0c00 (2026-10-15T22:55Z)

candidate-guard (before any block):

```text
CANDIDATE OK candidate=24c0c00038f2d15af4b55f178ea44e680c1f2c58 head=c8afb944b3da4c927ed1b150c38ddf4e40d9cfe0 descendant_commits=6 (reporting-only)
```

`materialize 24c0c00038f2d15af4b55f178ea44e680c1f2c58`: runner copy
`~/.b3/phase54-runner/plugin/vibe-check` := `24c0c00…:plugins/vibe-check` (git archive); runner
settings from the same commit. `identity` (all three clone dirs, first attempt, no refusal):

```text
IDENTITY OK manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 check_digest=70560d0938b3615d998851f227f0d2c0d88634757f6c1c155cb8b7de9e5cdd81 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58
```

`park-memory`: none of the three clone paths had auto-memory; park record
`~/.b3/automemory-parked-phase54-live-1792104909`.

## Cache

owner installed cache (before the sweep, 2026-10-15T22:10Z):
`~/.claude/plugins/cache/thejuran/vibe-check/2.11.1` fingerprint
`f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3` (= the v2.11.1 release).
Owner config sha256 before: `installed_plugins.json` `6a9cd0aa…`, `known_marketplaces.json`
`eafbfd5e…`, `settings.json` `3297ded3…`.

### Restart on 24c0c00 — owner cache before the sweep (2026-10-15T22:52Z)

`~/.claude/plugins/cache/thejuran/vibe-check/2.11.1` fingerprint
`f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3` (unchanged since the first
attempt). Owner config sha256: `installed_plugins.json` `6a9cd0aa…`, `known_marketplaces.json`
`eafbfd5e…`, `settings.json` `3297ded3…`.

### Restart on 24c0c00 — owner cache after the sweep (2026-10-16T01:44Z)

Fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3`, equal to the value
before the sweep. Owner config sha256 `6a9cd0aa…`, `eafbfd5e…`, `3297ded3…`, unchanged. No tmux
session left running; all three clones back on their start branch (roonseek `2370f0b`,
seedsyncarr `3dc75c7`, triggarr `4a154be`), `git status` clean. `restore-memory`: BLOCK OK. No clone
had auto-memory before the window; the 16 empty memory dirs the measured sessions created (0 files
in total) are kept as evidence in `~/.b3/automemory-parked-phase54-live-1792104909`.

## Deviations

### SWEEP STOPPED — 2026-10-15T22:11Z — identity check refuses every run once the session is alive

**What happened (first case, `reach-new-1` run-1).** `preflight`, `fresh`, `launch` and the
in-session `session` check all printed IDENTITY OK (so the 54-09 session-process check works
live). Claude started in the tmux pane; the one-time folder-trust prompt was accepted for the
disposable clone; `/clear` was sent. The next check, at `pre`, refused:

```text
setting differs: enabled_plugins.bm@gsd-plugin
setting differs: enabled_plugins.codex@openai-codex
setting differs: enabled_plugins.frontend-design@claude-plugins-official
setting differs: enabled_plugins.model-gateway@eigenwise-toolshed
setting differs: enabled_plugins.phi-compli@thejuran
setting differs: enabled_plugins.superpowers@claude-plugins-official
setting differs: gateway.tree_sha256
file differs: codex-companion (manifest 91961610b8da live f88f408c53dd)
IDENTITY MISMATCH — STOPPING
IDENTITY MISMATCH (pre) — STOPPING
```

`run_case.sh` stopped (exit 4 path, `RUN_CASE: STOP — pre`). No keystroke reached a review, no
run directory was created (`pre` refuses before `mkdir`), so there is nothing to `fail`.

**Cause (investigated, reproduced).** Claude Code 2.1.281 writes a runtime marker
`.in_use/<pid>` (a directory holding one 52-byte file per running claude process) into the
install directory of every enabled plugin while a session runs. The measured session (pid 42926)
added `.in_use/42926` to all six enabled plugins plus the codex companion and the gateway. The
identity check hashes each enabled plugin's install tree with `freeze_common.live_files`.
`freeze_common.EXCLUDED_NAMES = (".in_use",)` intends to exclude that marker, but `live_files`
applies `EXCLUDED_NAMES` to file names only. The directory form `.in_use/` is walked and every
`.in_use/<pid>` file is hashed. The unit test (`test_freeze_common.py::test_live_files_honors_excludes`)
writes `.in_use` as a plain file, so it never exercised the real directory shape.

Reproduction: with the measured session exited (`/exit`, pid gone) its marker disappeared and the
`identity` block printed IDENTITY OK again (same manifest_id/check_digest). Three other
long-running owner claude processes (pids 44375, 48371, 51562, started 2026-10-12/14) have their
own markers in the same directories, and these were already present when the draft manifest was
generated. The identity therefore depends on which claude processes are running: every measured
session makes `pre` and `post` refuse, and any owner session that starts or exits does too.

**Scope.** The runner copy is not affected: `~/.b3/phase54-runner/plugin/vibe-check` received no
marker, because the `--plugin-dir` copy is not an installed plugin. `score43.runtime_fingerprint`
is not affected in practice: it walks only the runtime subfolders, and the marker sits at the
install root. Only the user-level `enabled_plugins`, gateway and codex-companion identities are
affected (all three go through `freeze_manifest._plugin_identity` -> `freeze_common.live_files`).

**Not done (D-23 / D-27).** No code change was made. The check was not bypassed. No marker was
deleted (they belong to live owner sessions). Making the check pass needs a change to a covered
file (`docs/design/freeze-v2.12/tools/freeze_common.py`: prune `.in_use` directories as well as
files), so the sweep is stopped and reported. That fix means a new candidate, a regenerated draft
manifest and a restart from 54-10 Task 1.

**Clean-up.** The measured session was exited (`/exit`) and its tmux session killed. `revert
reach-new-1` returned the triggarr clone to `main@4a154be`, status clean. No `.planning/HANDOFF.json`
and no clone auto-memory dir were written. `restore-memory` closed the window (nothing had been
parked; the park record was removed so a restart can run `park-memory` again). Owner cache at the
stop (2026-10-15T22:12Z): fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3`,
equal to the value before; config sha256 `6a9cd0aa…`, `eafbfd5e…`, `3297ded3…`, unchanged.

### Restart on 24c0c00 — no stop (2026-10-15T22:55Z to 2026-10-16T01:44Z)

None. All 16 cases ran once in the pre-registered order with no exit 4, no unexpected card,
prompt or permission request, and no `fail`. **The `.in_use` fix held live:** `pre` and `post`
printed IDENTITY OK on every case while the measured session was running (32 checks with a live
session, plus `preflight`, `launch` and the in-pane `session` check per case). The `check_digest`
value differs between runs (`ea7ab2d4…` for the first case, a new value after each reporting
commit) because the digest covers the repo HEAD; every run's `manifest_id` and `candidate_sha`
equal the draft manifest's, which is what `post` and the tally compare. The candidate guard
printed `CANDIDATE OK` after every run commit (last: head `5e00d238…`, 22 descendant commits,
reporting-only).

## Tally

Restart on candidate 24c0c00 (targeted live check — not release evidence), 2026-10-16T01:45Z:

`python3 docs/design/freeze-v2.12/tools/freeze_tally.py dev-tally --runs-root docs/design/reachability-dev/runs-phase54-live --manifest docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`
— exit 0. No `stale:` or `missing:` line was printed (the tool prints one per affected run and
refuses on any), so stale 0, missing 0; runs 16. Every `run-1/fingerprint.txt` names manifest_id
`98af8754…`, candidate_sha `24c0c00…` and runtime_fingerprint `c046f0cf…` (16 of 16).

```text
reach-new-1 run-1 alarms=5 nv=0 fired=yes cards=2
reach-new-2 run-1 alarms=1 nv=0 fired=yes cards=2
reach-unchanged-1 run-1 alarms=1 nv=0 fired=yes cards=2
reach-unchanged-2 run-1 alarms=0 nv=0 fired=no cards=0
should-quiet-1 run-1 alarms=0 nv=0 fired=no cards=0
should-quiet-2 run-1 alarms=0 nv=1 fired=yes cards=2
should-quiet-3 run-1 alarms=0 nv=0 fired=no cards=0
should-quiet-4 run-1 alarms=1 nv=1 fired=yes cards=2
should-quiet-5 run-1 alarms=0 nv=0 fired=no cards=0
should-quiet-6 run-1 alarms=1 nv=0 fired=yes cards=2
should-quiet-7 run-1 alarms=1 nv=1 fired=yes cards=2
third-organic-should-catch run-1 alarms=1 nv=0 fired=yes cards=2
triggarr-autoescape run-1 alarms=1 nv=0 fired=yes cards=2
triggarr-secret-in-logs run-1 alarms=2 nv=0 fired=yes cards=2
triggarr-session-rotation run-1 alarms=2 nv=0 fired=yes cards=2
triggarr-settings-form-split run-1 alarms=2 nv=0 fired=yes cards=2
runs: 16
fired runs: 12
alarms: 18
needs-verification items: 3
owner questions: 24 (unavailable for 0 runs)
fingerprints seen: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
required fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
```

(The tool's own label line reads `development rehearsal - not release evidence`; these runs are
targeted live checks, equally not release evidence.)

Three totals, never summed (R13): **visible alarms 18 · Needs-verification items 3 · owner
questions 24** (24 = 2 measurement cards on each of the 12 runs that showed the fix-loop card; the
4 clean runs showed none; counted from `AskUserQuestion` calls in each main transcript and equal to
the tally's `cards`). Separately: **weak co-located remarks dropped 12** across 16 runs (Phase 53:
16), never summed with the others.

Phase 53 final for comparison: alarms 17 · NV 2 · owner questions 24 · fired runs 10.

**Burden (owner correction, 2026-10-16):** This rehearsal shows no owner-burden improvement (owner questions 24 → 24; headline quiet cases alarmed 3/6 vs 1/6) and a substantial risk of missing Phase 55's false-alarm target (≤3/18). should-quiet-2 stays counted as a fire on a should-quiet case (no exemption).

Catches: 7/7 kept (5/5 B3, 2/2 development), every credit from an alarm row, none from an NV row.
Quiet-shaped: 4/9 quiet (Phase 53: 6/9). Headline B3 quiet set (should-quiet-1..6): 3/6 fired on
this single run (Phase 53 final: 1/6; Phase 49: 5/18 runs).

## Per case

Before = Phase-53 signed-off final run (`NOTES-phase53-dev.md` `## Tally`, fingerprint `5bee4c11…`);
after = this run (candidate 24c0c00, fingerprint `c046f0cf…`). Changed outcomes in **bold**.

| case | role | before: alarms / NV / fired / cards / catch | after: alarms / NV / fired / cards / catch |
|---|---|---|---|
| reach-new-1 | catch (dev) | 4 / 0 / yes / 2 / credit 453bc76570c9 | **5** / 0 / yes / 2 / credit 1307c74d1331 |
| reach-new-2 | catch (dev) | 1 / 0 / yes / 2 / credit 3f078fc6d4f6 | 1 / 0 / yes / 2 / credit 13a2934ef82f |
| reach-unchanged-1 | quiet (dev) | 2 / 0 / yes / 2 / — | **1** / 0 / yes / 2 / — |
| reach-unchanged-2 | quiet (dev) | 0 / 0 / no / 0 / — | 0 / 0 / no / 0 / — |
| triggarr-secret-in-logs | catch | 2 / 0 / yes / 2 / credit 62cb389298ca | 2 / 0 / yes / 2 / credit 7867fa5685ed (second row **warning 91 -> critical 100**) |
| triggarr-autoescape | catch | 1 / 0 / yes / 2 / credit 02babc676ff2 | 1 / 0 / yes / 2 / credit 1a9bf42cf875 |
| third-organic-should-catch | catch | 1 / 0 / yes / 2 / credit 2cc1dbe9a612 | 1 / 0 / yes / 2 / credit 752a9cf1ec7f |
| triggarr-session-rotation | catch | 2 / 0 / yes / 2 / credit 312fd3c4c345 | 2 / 0 / yes / 2 / credit 1ad9703f6d61 |
| triggarr-settings-form-split | catch | 2 / 0 / yes / 2 / credit 6b98d7648011 | 2 / 0 / yes / 2 / credit 0aa760122e32 |
| should-quiet-1 | quiet | 0 / 0 / no / 2 / — | 0 / 0 / no / **0** / — |
| should-quiet-2 | quiet | 0 / 0 / no / 2 / — | 0 / **1** / **yes** / 2 / — |
| should-quiet-3 | quiet | 0 / 0 / no / 0 / — | 0 / 0 / no / 0 / — |
| should-quiet-4 | quiet (known residual) | 1 / 2 / yes / 2 / — | 1 / **1** / yes / 2 / — |
| should-quiet-5 | quiet | 0 / 0 / no / 0 / — | 0 / 0 / no / 0 / — |
| should-quiet-6 | quiet | 0 / 0 / no / 0 / — | **1** / 0 / **yes** / **2** / — |
| should-quiet-7 | quiet (excluded, #001) | 1 / 0 / yes / 2 / — | 1 / **1** / yes / 2 / — |

A changed lead lane or stable hash on a credited row (same site, same defect) is not an outcome
change; the credited band is critical 100 on both sides for all seven catch cases.

**Cause test (scorer).** All 16 live runs were re-scored offline from their archived state +
transcript (`replay.reconstruct_envelope`) through both the Phase-53 scorer (`rev:ebcd3e4`, sha256
`525c5e83…`) and the candidate scorer (`rev:24c0c00`, sha256 `ea6b0417…`): **0 of 16 runs differ**,
and both reproduce each run's archived alarm/NV counts exactly. So no changed outcome above comes
from the one scorer change (R1 placeholder rule); every difference is in what the lanes wrote.

**Cause test (R1 / schema sentence).** No lane output in any of the 16 transcripts carries a
`needs_verification` field whose value is wholly `N/A`, `none` or `-`, and none carries an empty
`{}`; lanes that had nothing to verify wrote `null` (not touched by R1). The three NV dicts that
reached the scorer (should-quiet-2, -4, -7) have concrete trigger/path/consequence values. So the
R1 rule had nothing to act on in this sweep. The one-sentence schema addition (placeholders
count as absent) is in the prompt every lane reads; one run per case cannot isolate its influence
on what the lanes wrote. The finalize-routing change (R2) runs only in Finalize mode, which no
measured run reaches (`Stop here…` -> `Abandon`). **Conclusion (wording corrected by the owner,
2026-10-16): no difference attributable to Phase 54 was demonstrated; identical re-scoring rules out scorer effects, but the runtime schema-wording change (agent-output-schema.md) is not isolated from lane behavior.** Each change is reported below and in the R4 table for the owner's
decision.

## Lost catch investigation

**No catch was lost on candidate 24c0c00.** Every Phase-53 catch was reproduced:

- B3 (5/5): `triggarr-secret-in-logs` (7867fa5685ed, base.py:233), `triggarr-autoescape`
  (1a9bf42cf875, routes.py:45), `third-organic-should-catch` (752a9cf1ec7f, view-file.service.ts:307),
  `triggarr-session-rotation` (1ad9703f6d61, routes.py:1567), `triggarr-settings-form-split`
  (0aa760122e32, settings.html:18) — each a `catch-candidates` row at the keyed site naming the
  keyed causal failure, critical 100, alarm (hand AXIS lines under each run).
- Development (2/2): `reach-new-1` (1307c74d1331, routes.py:1689), `reach-new-2` (13a2934ef82f,
  notification-bell.component.html:28) — each a `dev-catch-candidates` row at the keyed site.

No case was run more than once (`runs-phase54-live/` has only `run-1` dirs and no `attempts/`).
The replay guard (54-10 re-run) kept every protected catch: 25 kept + 1 ledger-amended, 0 regressed.
No blocking condition.

The one divergence carried from Phase 53 is unchanged: on `triggarr-autoescape` the lead mechanism
is a TypeError at import on the installed Starlette, where the key describes a silent autoescape
no-op; the row names the autoescape/XSS consequence the key requires.

## Changed quiet-shaped outcomes (for the owner)

Not lost catches; recorded here because they change what the owner signed off.

- **should-quiet-2: quiet -> FIRED (1 NV).** The bugs lane raised an NV item that saving settings
  fails because `ConfigService.set` still sends GET to a route that is POST-only. Checked in the
  disposable clone at the case's base `84aff27`: the backend already registers
  `/server/config/set` with `add_post_handler`, and `config.service.ts:68` still sends GET. That
  is the owner's own mid-migration state (the backend change landed before this commit); the diff
  only widens `RestService.post(url)` to `post(url, body?)` and touches neither file. So the item
  describes a real break that predates the change, raised against a clean feature diff, which
  counts as a fire on a should-quiet case. First fire on this case in the record (Phase 49 0/3,
  Phase 53 quiet).
- **should-quiet-6: quiet -> FIRED (1 alarm).** Codex warning "Wire the accepted timeout into the
  shutdown drain" (the new config field has no consumer). The Phase-53 targeted run on the
  signed-off build fired the same way (codex critical + bugs NV); only the Phase-53 final run was
  quiet, and the owner's sign-off recorded both outcomes as same-build variability. Phase 49: 3/3.
- **should-quiet-7 (excluded, #001): NV 0 -> 1.** Alarm unchanged (the settings-save overwrite);
  a new bugs NV item that the saved timeout has no consumer. Its exclusion stands.
- **should-quiet-4 (known residual): NV 2 -> 1.** Same numeric-host bypass alarm; the two
  legacy-value NV items now arrive as one item naming both shapes.
- **reach-unchanged-1: alarms 2 -> 1.** The same key-correction defect, now one merged row.
- **should-quiet-1: owner questions 2 -> 0.** Still quiet; no fix-loop card this time.
- **reach-new-1: alarms 4 -> 5** (a new codex warning "The newly exposed recovery flow has no token
  consumer" at routes.py:1617; catch kept). **triggarr-secret-in-logs:** second row warning 91 ->
  critical 100 (alarm count unchanged; catch kept).

## Schema sentence and R1 in this sweep

No live run exercised a placeholder NV value (see `## Per case`, cause test): 0 placeholder fields,
0 empty dicts across 16 transcripts; 3 NV dicts reached the scorer, all concrete. The R1 rule
therefore did not fire live; it remains proven by `TestNeedsVerificationPlaceholders` (54-01) and
by this sweep's 0-of-16 scorer-difference result.

## Owner decision — 2026-10-16 (R4, candidate 24c0c00038f2)

Verbatim, as recorded in `R4-BEFORE-AFTER.md` `## Owner decision`:

> “1 — Approve the R4 comparison and continue to the release gates, with two corrections to the record.- “No difference attributable to Phase 54 was demonstrated” is supported. “None was caused by Phase 54” is too strong: identical rescoring rules out scorer effects, but doesn’t isolate the runtime schema wording’s influence on what reviewers wrote.- 3/6 quiet cases alarmed, and owner questions stayed at 24. Record that plainly: this rehearsal shows no burden improvement and a substantial risk of missing Phase 55’s false-alarm target.Keep should-quiet-2 counted as an alarm; its pre-existing nature earns no exemption. Don’t change keys, tune prompts, or rerun selectively for better results.This approves proceeding—not declaring the milestone met. The remaining release gates, including the separate live close-out checks, must still pass before freeze.”

## Runs

### live/reach-new-1/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 5
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 1573 | critical | 100 | 25bbb9f3e38a |
| bugs | triggarr/web/routes.py | 1577 | warning | 94 | 382c05cda080 |
| codex-adversarial | triggarr/web/routes.py | 1689 | critical | 100 | 1307c74d1331 |
| impact | triggarr/web/routes.py | 1580 | warning | 80 | 8655981d9c9a |
| codex-adversarial | triggarr/web/routes.py | 1617 | warning | 94 | 53b1a7cd70a4 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

keyed defect: triggarr/web/routes.py:1689-1692 (reset_request_post) logs the newly minted password-reset token at WARNING into the unchanged logging path: the buffer sink (triggarr/logging.py:72-84) copies it into log_buffer unredacted because the token is not in the collect_secrets redaction list, and the unchanged in-app log viewer (routes.py:1079-1094) and dashboard render that buffer, so anyone who can read the log viewer can read a live reset token and complete a password reset.
label: development rehearsal - not release evidence
| agent | file | line | band | score | stable_hash | nv | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 1689 | critical | 100 | 1307c74d1331 | no | Reset tokens are disclosed through the web log viewer | codex-adversarial: Reset tokens are disclosed through the web log viewer; compliance: Password reset token logged in cleartext, bypassing the project's secret-redaction sink; security: Reset token leaks into HTTP-rendered log viewer, contradicting the code's own "never in an HTTP response" invariant; security: Plaintext reset token written to general application log stream (docker logs) |  |
candidates at site: 1 (alarms 1, needs-verification 0)

AXIS: credit — row 1307c74d1331 (alarm, critical 100) at routes.py:1689 — "Reset tokens are disclosed through the web log viewer"; members compliance "Password reset token logged in cleartext, bypassing the project's secret-redaction sink", security "Reset token leaks into HTTP-rendered log viewer". Location AND causal failure match.

vs Phase 53 final: catch kept (credited row now led by codex-adversarial, 1307c74d1331; Phase 53 led by security, 453bc76570c9 — same site, same defect). Alarms 4 -> 5; the extra alarms are off the keyed defect (mkstemp fd/permission rows at 1573-1580, as before, plus a codex warning at 1617). NV 0 -> 0. Cards 2 -> 2 (AskUserQuestion in the main transcript). Weak co-located notes dropped: 2. Run 17m24s; fix-loop card after 1022s; `Stop here…` -> `Abandon` by label. `pre` and `post` IDENTITY OK with the session alive (first live pass of the `.in_use` fix). Statusline: 84 samples, all `claude-fable-5-1[1m]`, context_window_size 1000000.

### live/reach-new-2/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/angular/src/app/pages/main/notification-bell.component.html | 28 | critical | 100 | 13a2934ef82f |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

keyed defect: src/angular/src/app/pages/main/notification-bell.component.html:28 now binds unchanged server- and remote-influenced notification text with [innerHTML] instead of {{ notif.text }} interpolation, so markup in those strings is parsed as HTML in every open UI (HTML injection): Angular's sanitizer keeps links, images and formatting, so injected markup can render attacker-controlled links or images in a trusted UI element.
label: development rehearsal - not release evidence
| agent | file | line | band | score | stable_hash | nv | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|---|
| bugs | src/angular/src/app/pages/main/notification-bell.component.html | 28 | critical | 100 | 13a2934ef82f | no | Removing text-interpolation escaping lets server and remote-scan error strings inject HTML markup (sanitizer is now the only defense against script execution) | bugs: Removing text-interpolation escaping lets server and remote-scan error strings inject HTML markup (sanitizer is now the only defense against script execution); security: Notification text switched from auto-escaped interpolation to raw [innerHTML], reverting prior XSS hardening; codex-adversarial: Notification HTML injection permits deceptive links; bugs: Notification text containing '<' or '&' is mangled or dropped when parsed as HTML; architecture: Notification.text silently changes from plain text to rendered HTML for every producer; impact: Notification text switched from escaped interpolation to [innerHTML]: server and remote-host error strings are now parsed as HTML (link/image injection); impact: Script-execution protection now depends on Angular's default sanitizer instead of guaranteed escaping |  |
candidates at site: 1 (alarms 1, needs-verification 0)

AXIS: credit — row 13a2934ef82f (alarm, critical 100) at notification-bell.component.html:28 — "Removing text-interpolation escaping lets server and remote-scan error strings inject HTML markup"; members security "switched from auto-escaped interpolation to raw [innerHTML]", impact "server and remote-host error strings are now parsed as HTML (link/image injection)". Location AND causal failure (HTML injection) match; scored on HTML injection only.

vs Phase 53 final: catch kept (credited row now led by bugs, 13a2934ef82f; Phase 53 led by impact, 3f078fc6d4f6 — same site, same defect). Alarms 1 -> 1, NV 0 -> 0, cards 2 -> 2. Weak co-located notes dropped: 0. Run 13m07s; fix-loop card after 767s; `Stop here…` -> `Abandon` by label. Statusline: 72 samples, all `claude-fable-5-1[1m]`, context_window_size 1000000.

### live/reach-unchanged-1/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/roonseek/web/_filter_overrides.py | 73 | critical | 100 | b1c765a372c6 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs Phase 53 final: "quiet" (retained expectation, owner sign-off) -> FIRED (1 alarm, 0 NV), as in Phase 53 (2 alarms). The single alarm b1c765a372c6 (codex-adversarial critical at `_filter_overrides.py:73`, "Removed parser is still imported by the test suite"; members architecture, bugs) is the same one real new defect recorded as the dated key correction — `parse_optional_int` deleted while `tests/test_filter_overrides.py:13` still imports it. Phase 53 showed it as two rows (bugs critical at :73 + architecture warning at the test import); here the architecture member merged into the one row, so alarms 2 -> 1. None of the keyed already-reachable weaknesses (a)-(c) raised. Cards 2 -> 2. Run 15m42s; fix-loop card after 917s; `Stop here…` -> `Abandon` by label. Statusline: 71 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/reach-unchanged-2/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs Phase 53 final: "quiet" -> quiet (0 alarms, 0 NV), unchanged. Clean review: no fix-loop card (cards 0 -> 0). Run 7m43s. Statusline: 71 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/triggarr-secret-in-logs/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 7867fa5685ed |
| architecture | triggarr/clients/base.py | 252 | critical | 100 | 0dbc67cd110e |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 7867fa5685ed | Raw HTTP exceptions expose URL credentials in logs | codex-adversarial: Raw HTTP exceptions expose URL credentials in logs; bugs: Reverts security fix d47b4c2: raw HTTPStatusError logged, exposing the full instance URL (and any URL credentials) in logs and the web UI log viewer; architecture: Diff exactly reverts security fix d47b4c2 and drops the established exception-sanitization pattern; compliance: Reverts named security fix, reintroduces raw exception logging; impact: Reverts security fix d47b4c2: raw HTTPStatusError logged again, which can expose credentials in the URL in stderr and the in-UI log viewer; security: Exception objects now logged verbatim in error/warning paths |  |
| architecture | triggarr/clients/base.py | 252 | critical | 100 | 0dbc67cd110e | ValidationError now logged raw instead of as an error count, unlike every other pydantic log site | architecture: ValidationError now logged raw instead of as an error count, unlike every other pydantic log site; codex-adversarial: Validation errors disclose upstream response data; compliance: Reverts named security fix, reintroduces raw ValidationError logging; bugs: Reverts sanitized ValidationError log: raw pydantic error text, including input values from the response body, now reaches logs and the web UI buffer; impact: Reverts sanitization of pydantic.ValidationError: response body values now logged verbatim (data exposure / log injection) |  |
candidates at site with band >= floor: 2

AXIS: credit — row 7867fa5685ed (alarm, critical 100) at clients/base.py:233 (keyed bug line) — "Raw HTTP exceptions expose URL credentials in logs"; members bugs "raw HTTPStatusError logged, exposing the full instance URL (and any URL credentials) in logs and the web UI log viewer", impact "can expose credentials in the URL in stderr and the in-UI log viewer". Location AND causal failure (secret in the exception URL leaked into logs) match.

vs Phase 53 final: catch kept (credited row 7867fa5685ed; Phase 53 62cb389298ca, same lead lane and line). Alarms 2 -> 2, NV 0 -> 0, cards 2 -> 2. Second row at base.py:252 (raw pydantic ValidationError logged): Phase 53 architecture warning 91 (021700bd8847) -> now architecture critical 100 (0dbc67cd110e; members codex-adversarial, compliance, bugs, impact). Not the credited row; the alarm count is unchanged. Weak co-located notes dropped: 3. Run 13m56s; fix-loop card after 811s; `Stop here…` -> `Abandon` by label. Statusline: 82 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/triggarr-autoescape/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/web/routes.py | 45 | critical | 100 | 1a9bf42cf875 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| architecture | triggarr/web/routes.py | 45 | critical | 100 | 1a9bf42cf875 | Reverts to the Jinja2Templates **env_options form, which the pinned Starlette no longer accepts | architecture: Reverts to the Jinja2Templates **env_options form, which the pinned Starlette no longer accepts; codex-adversarial: Template constructor crashes application startup; language-python: Jinja2Templates() call passes unsupported autoescape kwarg, crashes on import; compliance: Revert of autoescape fix passes unsupported kwarg, crashing app at import; bugs: Jinja2Templates(autoescape=True) raises TypeError at import: the installed Starlette no longer accepts **env_options; impact: Reverting to Jinja2Templates(autoescape=True) raises TypeError at import, so the app cannot start; framework-fastapi: Jinja2Templates() passed unsupported autoescape kwarg, crashes app at import; security: Reverted Jinja2 autoescape fix reintroduces XSS exposure (and breaks startup on the pinned Starlette version); impact: Autoescape (the XSS protection) now relies on an old Starlette API instead of an explicit jinja2.Environment |  |
candidates at site with band >= floor: 1

AXIS: credit — row 1a9bf42cf875 (alarm, critical 100) at routes.py:45 (keyed bug line) — survivor "Reverts to the Jinja2Templates **env_options form, which the pinned Starlette no longer accepts"; members security "Reverted Jinja2 autoescape fix reintroduces XSS exposure (and breaks startup on the pinned Starlette version)", impact "Autoescape (the XSS protection) now relies on an old Starlette API". The escaping/XSS consequence is named at the keyed line. As in both Phase-53 runs, the lead mechanism is a TypeError at import on the installed Starlette (the key describes a silent no-op); both are the version-dependent loss of autoescape.

vs Phase 53 final: catch kept (credited row now led by architecture, 1a9bf42cf875; Phase 53 led by compliance, 02babc676ff2 — same line, same divergence recorded then). Alarms 1 -> 1, NV 0 -> 0, cards 2 -> 2. Run 9m47s; fix-loop card after 571s; `Stop here…` -> `Abandon` by label. Statusline: 86 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/third-organic-should-catch/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 752a9cf1ec7f |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 752a9cf1ec7f | Completed extracted files display progress above 100% and lose completion indicators | codex-adversarial: Completed extracted files display progress above 100% and lose completion indicators; architecture: Removing the service-layer clamp breaks the 0-100 contract that view consumers depend on; language-typescript: Math.min(100, ...) clamp removed from percentDownloaded, reverting a deliberate fix and failing existing regression tests; bugs: Removing the 100% clamp lets extracted files show progress above 100% and lose their Done state; impact: Removing the Math.min(100, ...) clamp brings back the >100% progress display (e.g. '199%') and breaks the 'Done' and success states for extracted archives; bugs: Downstream checks for exactly 100 never match once the value can go above 100 |  |
candidates at site with band >= floor: 1

AXIS: credit — row 752a9cf1ec7f (alarm, critical 100) at view-file.service.ts:307 (keyed bug lines 307-309) — "Completed extracted files display progress above 100% and lose completion indicators"; members language-typescript "Math.min(100, ...) clamp removed from percentDownloaded", bugs "Downstream checks for exactly 100 never match once the value can go above 100". Names the missing clamp / out-of-range value. Location AND causal failure match.

vs Phase 53 final: catch kept (credited row now led by codex-adversarial at :307, 752a9cf1ec7f; Phase 53 2cc1dbe9a612 at :308 — same keyed hunk, same defect). Alarms 1 -> 1, NV 0 -> 0, cards 2 -> 2. Run 7m01s; fix-loop card after 406s; `Stop here…` -> `Abandon` by label. Statusline: 82 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-1/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs Phase 53 final: "quiet" -> quiet (0 alarms, 0 NV), unchanged verdict. Owner questions changed: Phase 53 showed the fix-loop card for sub-Warning rows (2 cards); this run was a clean review with no fix-loop card (0 cards). Run 6m05s. Statusline: 73 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-2/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 0
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/angular/src/app/services/utils/rest.service.ts | 59 | needs-verification | 0 | f2c7d4d9ed83 |

vs Phase 53 final: "quiet" -> FIRED (0 alarms, 1 NV) — a fail on a should-quiet case (Phase 49: 0/3 fired; Phase 53 final: quiet). Source: NV f2c7d4d9ed83 (bugs, `rest.service.ts:59`) — "New POST body parameter has no caller: ConfigService.set still sends GET to a route that is now POST-only, so saving settings fails" (trigger/path/consequence all concrete). Checked in the clone at the case's base `84aff27`: the backend already registers `/server/config/set` with `add_post_handler` and `config.service.ts:68` still sends a GET — the owner's own mid-migration state before this diff. The diff only widens `post(url)` to `post(url, body?)` and changes neither file, so the item describes a pre-existing condition outside the change. Cards 2 -> 2 (Phase 53 showed the card for sub-Warning rows). Run 6m17s; fix-loop card after 361s; `Stop here…` -> `Abandon` by label. Statusline: 80 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-3/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs Phase 53 final: "quiet" -> quiet (0 alarms, 0 NV), unchanged. Clean review (cards 0 -> 0). Run 5m59s. Statusline: 74 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/triggarr-session-rotation/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 1567 | critical | 100 | 1ad9703f6d61 |
| bugs | triggarr/web/routes.py | 1581 | warning | 90 | 50816525e11a |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 1567 | critical | 100 | 1ad9703f6d61 | Password change no longer rotates session_secret, so stolen or old session cookies stay valid for up to 30 days (session hijack persists) | impact: Password change no longer rotates session_secret, so stolen or old session cookies stay valid for up to 30 days (session hijack persists); codex-adversarial: Stolen session cookies retain access after password changes; architecture: change_password no longer follows the credential-change pattern that reset_confirm_post mirrors; bugs: Password change no longer rotates session_secret, so other sessions stay valid after the change; security: Password change no longer invalidates existing sessions (revert of documented session-secret rotation); impact: Password change and reset now handle existing sessions differently |  |
| bugs | triggarr/web/routes.py | 1581 | warning | 90 | 50816525e11a | Existing rotation and eviction tests will fail against this change | bugs: Existing rotation and eviction tests will fail against this change; impact: Removing the rotation and re-issue breaks five existing auth tests that assert eviction behavior; security: Removed security-relevant audit log line for password change |  |
candidates at site with band >= floor: 2

AXIS: credit — row 1ad9703f6d61 (alarm, critical 100), listed at the keyed site by `catch-candidates` (routes.py:1567) — "Password change no longer rotates session_secret, so stolen or old session cookies stay valid for up to 30 days (session hijack persists)"; members codex-adversarial "Stolen session cookies retain access after password changes", security "no longer invalidates existing sessions". Location AND causal failure (session eviction lost) match.

vs Phase 53 final: catch kept (credited row now led by impact, 1ad9703f6d61; Phase 53 led by codex-adversarial, 312fd3c4c345 — same line, same defect). Alarms 2 -> 2 (second alarm 50816525e11a, bugs warning 90 at routes.py:1581, existing rotation/eviction tests will fail — as Phase 53's 494fa8e8b5c1). NV 0 -> 0, cards 2 -> 2. Weak co-located notes dropped: 1. Run 10m02s; fix-loop card after 586s; `Stop here…` -> `Abandon` by label. Statusline: 80 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/triggarr-settings-form-split/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/templates/settings.html | 134 | warning | 94 | 0d791969c869 |
| impact | triggarr/templates/settings.html | 18 | critical | 100 | 0aa760122e32 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| bugs | triggarr/templates/settings.html | 134 | warning | 94 | 0d791969c869 | Save Settings now posts without the General fields, so every save silently resets General settings to defaults | bugs: Save Settings now posts without the General fields, so every save silently resets General settings to defaults |  |
| impact | triggarr/templates/settings.html | 18 | critical | 100 | 0aa760122e32 | This diff undoes fix 542d5dd: clicking 'Save Settings' resets every General setting to its default | impact: This diff undoes fix 542d5dd: clicking 'Save Settings' resets every General setting to its default; compliance: Reverts General-section form to the exact broken pattern CLAUDE.md's own convention and a prior fix commit rejected; architecture: This change undoes fix 542d5dd: General fields are back in a form with no Save button, so saving never sends them; codex-adversarial: Restore General fields to the Save Settings submission; bugs: General settings form has no submit button and cannot be submitted |  |
candidates at site with band >= floor: 2

AXIS: credit — row 0aa760122e32 (alarm, critical 100) at settings.html:18 (keyed hunk 15-28) — "This diff undoes fix 542d5dd: clicking 'Save Settings' resets every General setting to its default"; members architecture "General fields are back in a form with no Save button, so saving never sends them", bugs "General settings form has no submit button and cannot be submitted". Row 0d791969c869 (warning 94) at settings.html:134 (keyed hunk 131-137) names the same fields-not-submitted reset. Location AND causal failure (broken form association, silent data loss on save) match.

vs Phase 53 final: catch kept (credited row now led by impact, 0aa760122e32; Phase 53 led by architecture, 6b98d7648011 — same line, same defect). Alarms 2 -> 2 (same lines and bands), NV 0 -> 0, cards 2 -> 2. Run 10m05s; fix-loop card after 586s; `Stop here…` -> `Abandon` by label. Statusline: 83 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-4/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | 70d4464aa520 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | needs-verification | 0 | edb7d2b25e80 |

vs Phase 53 final: "quiet" (QUIET-03; known residual for this release, owner sign-off) -> FIRED (1 alarm, 1 NV); Phase 53 FIRED (1 alarm, 2 NV). Alarm 70d4464aa520, codex-adversarial warning 94 at models/config.py:107 — "Alternate numeric IP notation bypasses metadata SSRF protection" (the same numeric-host bypass disagreement recorded at sign-off; Phase 53 37b2056f0936 at :108). NV edb7d2b25e80 (bugs, config.py:108) — "Upgrade compatibility: values the old config accepted (0.0.0.0, a scheme-less host:port, a disabled instance with a bad URL) now abort startup": the two Phase-53 legacy-value NV items (bugs b04b099a1960 + impact 5ded17410c7d) now arrive as one bugs item naming both shapes, so NV 2 -> 1. Cards 2 -> 2. Weak co-located notes dropped: 3. Run 13m27s; fix-loop card after 782s; `Stop here…` -> `Abandon` by label. Statusline: 82 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-5/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs Phase 53 final: "quiet" -> quiet (0 alarms, 0 NV), unchanged. Clean review (cards 0 -> 0). Run 5m01s. Statusline: 78 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-6/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 5646e628420f |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs Phase 53 final: "quiet, or at worst an NV item" -> FIRED (1 alarm, 0 NV) — a fail (Phase 49: 3/3 fired; Phase 53 targeted run on the signed-off build: FIRED, codex critical c93be6bfe251 + bugs NV; Phase 53 final: quiet). Alarm 5646e628420f, codex-adversarial warning 94 at models/config.py:139 — "Wire the accepted timeout into the shutdown drain"; members bugs "New config field has no consumer, so the scheduler still ignores it", "Saving settings silently resets a configured shutdown_drain_timeout to 60.0", "No upper bound, so a config value can exceed the Docker stop grace period". Same finding shape as the Phase-53 targeted run (codex lane on the unconsumed field). Cards 0 -> 2. Run 7m33s; fix-loop card after 436s; `Stop here…` -> `Abandon` by label. Statusline: 87 samples, all `claude-fable-5-1[1m]`, 1000000.

### live/should-quiet-7/run-1 — targeted live check — not release evidence

fingerprint: c046f0cf0b4d702fabd7e35aa7cd3ec12501fa9e12542f1e649a0668228f5fb9
identity: manifest_id=98af8754d5aed5b9d9a2d89b1e2d2b4839ad1e87f596d7621568a269f22dfd99 candidate_sha=24c0c00038f2d15af4b55f178ea44e680c1f2c58

alarms: 1
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 4d966837bba8 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | needs-verification | 0 | fcc0b38c0558 |

vs Phase 53 final: "quiet, or at worst an NV item" (excluded from the release verdict, SUPERSESSIONS #001, retained at sign-off) -> FIRED (1 alarm, 1 NV); Phase 53 FIRED (1 alarm, 0 NV). Alarm 4d966837bba8, bugs critical 100 at routes.py:550 — "Every settings save silently resets shutdown_drain_timeout to 60.0 because the form has no such input" (the same traced overwrite as Phase 53's 544b4b23813b). New NV fcc0b38c0558 (bugs, routes.py:550) — "Saved shutdown_drain_timeout has no consumer; the scheduler still uses only the env var read at import" (trigger/path/consequence concrete). NV 0 -> 1. Cards 2 -> 2. Weak co-located notes dropped: 3. Run 8m34s; fix-loop card after 496s; `Stop here…` -> `Abandon` by label. Statusline: 82 samples, all `claude-fable-5-1[1m]`, 1000000.

---

# Restart on candidate 2a6dbb4874b7 (54-11 restart #2)

Everything above this line is the record of the 302df48 attempt and the 24c0c00 sweep and its
owner decision. It is kept unchanged. Nothing from the 24c0c00 runs counts on this candidate
(D-21): those runs describe a superseded build and an environment without the S5/S6 containment.

## Pre-registration — restart on candidate 2a6dbb4 — 2026-10-17T15:14Z (before the first run)

Candidate 24c0c00 was superseded by the owner-approved batched fix (A1–A2, B1–B7, P1, S5–S10,
S11) and follow-ups 2b/2c (54-16/54-17). 54-10 re-run #4 selected a new candidate and regenerated
the draft manifest; this sweep starts over on it.

- **Candidate:** `2a6dbb4874b7521b66d53b2fbb1406dfb46dc230`, read from
  `docs/design/freeze-v2.12/evidence/CANDIDATE.json` (never `HEAD`). It equals the draft
  manifest's `candidate_sha`.
- **Manifest:** the regenerated draft at the same path,
  `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`, `manifest_id`
  `3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc`, used as `MANIFEST` for the
  whole sweep. Its B3 launch model is `claude-fable-5-1[1m]`, equal to `pin-model:` above; plugin
  `runtime_fingerprint` `c879892c…`. Pins unchanged: `claude --version` 2.1.281, `codex --version`
  0.153.4 (checked live 2026-10-17T15:14Z).
- **Owner condition met before the sweep (S5–S7, acceptance list `## Owner decision
  (supplemental table)`):** the synthetic live review is the two 54-10 containment proofs, both on
  this candidate and this manifest:
  - `evidence/containment-proof-b3.json` (4c8fbde): `candidate_sha` 2a6dbb4…, `manifest_id`
    3491dd4c…, verdict CONTAINMENT PROOF OK. Python scoring ran (format-53 state written by
    score.py), the local gateway served 94 turns, Codex joined (`codex_setup_ready` allowed,
    verdict needs-attention). Credential reads denied on Bash, Python, Node and the Read tool;
    unauthorized network denied on curl, Python urllib, Python raw socket, Node fetch and Node raw
    socket; env allowlist held; secret absent from the transcript.
  - `evidence/containment-proof-holdout.json` (696bed6): same candidate and manifest, CONTAINMENT
    PROOF OK, holdout review run VALID (`freeze_policy.py run-validity` exit 0).
- **Invalid-run rule (owner condition):** every run is judged by `post`'s
  `freeze_policy.py run-validity` (permission failure — a tool refusal or a sandbox violation —,
  incomplete review, or missing scorer output = INVALID). An invalid run is never a result: it is
  `fail`ed into `attempts/` and the slot is redone with the next run number on the same candidate,
  in a fresh run folder. It never counts as quiet or as a miss. A redo is the same case, the same
  candidate, the same keystrokes; it is not a selective rerun for a better outcome. A COMPLETED
  valid run is never rerun.
- **Sandboxing is an environment change** (owner condition). The Phase-53 rehearsal and the
  24c0c00 sweep ran without the S5/S6 containment (Seatbelt sandbox, network allowlist, credential
  deny rules, `env -i` session allowlist, codex plugin hook off). This sweep tests compatibility and
  shows outcome differences; it cannot attribute any single difference to the sandbox, or rule
  the sandbox out.
- **Run folders:** the 16 superseded 24c0c00 run dirs are moved, byte-for-byte, to
  `runs-phase54-live/superseded-24c0c00038f2/<case>/run-1` before the first run (their
  gitignored transcripts move with them and stay ignored). `pre` refuses an existing `run-1`, and
  `dev-tally` walks every `<case>/run-*` under the runs root, so the old dirs cannot stay in place.
  The new runs take `run-1`.
- **Disposable clones:** re-used, each on its start branch and `git status` clean at 15:14Z:
  roonseek `2370f0b`, seedsyncarr `3dc75c7`, triggarr `4a154be`.
- **Isolated runner:** re-materialized from 2a6dbb4 (`materialize`), runner settings from the same
  commit (the S5/S6 containment settings).
- **Everything else as the first pre-registration:** memory parked, owner cache untouched, one run
  per case in the same order (`reach-new-1`, `reach-new-2`, `reach-unchanged-1`,
  `reach-unchanged-2`, `triggarr-secret-in-logs`, `triggarr-autoescape`,
  `third-organic-should-catch`, `should-quiet-1`, `should-quiet-2`, `should-quiet-3`,
  `triggarr-session-rotation`, `triggarr-settings-form-split`, `should-quiet-4`, `should-quiet-5`,
  `should-quiet-6`, `should-quiet-7`), all 16, no retune, no key change, the same fixed
  keystrokes, the same comparison (before = Phase-53 signed-off final run; the 24c0c00 run shown
  alongside for reference) and the same lost-catch rule.
- **R4 wording rules (owner, 2026-10-16):** a changed row's cause reads "no difference
  attributable to Phase 54 was demonstrated" unless a specific cause is shown — never "not caused
  by Phase 54". Any burden change is stated plainly, with the risk to Phase 55's false-alarm bar
  (≤3/18). should-quiet-2 counts as an alarm when it fires. An R4 approval is not a declaration
  that the milestone is met.

### Owner cache — before the sweep (2026-10-17T15:14Z)

`~/.claude/plugins/cache/thejuran/vibe-check/2.11.1` fingerprint
`f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3` (unchanged since 2026-10-15).
Owner config sha256: `installed_plugins.json` `962a26ec…`, `known_marketplaces.json` `bf22ccb2…`,
`settings.json` `012ecb8d…` (different from the 2026-10-15/16 values; the owner's config changed
between sweeps; the identity check binds the effective settings either way).

## Candidate — restart on 2a6dbb4 (2026-10-17T15:16Z)

candidate-guard (before any block):

```text
CANDIDATE OK candidate=2a6dbb4874b7521b66d53b2fbb1406dfb46dc230 head=d3af6ad01f73f5d56dbf1b986880456d267465dc descendant_commits=8 (reporting-only)
```

(re-run after the pre-registration and the run-dir move: head `1ba9c79`, 10 descendants,
reporting-only.)

`materialize 2a6dbb4874b7521b66d53b2fbb1406dfb46dc230`: runner copy
`~/.b3/phase54-runner/plugin/vibe-check` := `2a6dbb4…:plugins/vibe-check` (git archive); runner
settings `~/.b3/phase54-runner/settings-measured.json` := `2a6dbb4…:docs/design/b3-ground-truth/b3-runner-v2.12/settings-measured.json`.
`identity` (all three clone dirs, first attempt, no refusal):

```text
IDENTITY OK manifest_id=3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc check_digest=829e68ccddf9df112d61a03ac565c0813e6864584ac6d3ca7de9ba8b009a1794 candidate_sha=2a6dbb4874b7521b66d53b2fbb1406dfb46dc230
```

`park-memory`: none of the three clone paths had auto-memory; park record
`~/.b3/automemory-parked-phase54-live-1792250123`.

## Runs — restart on 2a6dbb4 (`post` appends each run record below)

## Deviations — restart on 2a6dbb4

### SWEEP STOPPED — 2026-10-17T15:32Z — `post` cannot archive a Codex-joined run under the sandbox

**What happened (first case, `reach-new-1` run-1).** `preflight`, `fresh`, `launch`, the in-pane
`session` check and `pre` all printed IDENTITY OK (manifest_id 3491dd4c…, candidate 2a6dbb4…).
The review ran under the S5/S6 containment for 16m 5s with no unexpected card or permission
prompt; the fix-loop card came after 947 s and was answered `Stop here…` then `Abandon` by label.
`post` then ran:

```text
IDENTITY OK manifest_id=3491dd4c5712c8badbedc251e8bb29b08c651c07a4eeb22bc8747ed1108290bc check_digest=37304d49e3b00a043d3864c7dbe01765057b3b9b7238e518b93e71ef29d473c2 candidate_sha=2a6dbb4874b7521b66d53b2fbb1406dfb46dc230 (post)
OK one isolated pass at 345eaaad08d592376897c3d9a5c33ca173fdbbf8
captured 9 transcript file(s)
VALID RUN
unreadable input: ValueError
LANE ARCHIVE REFUSED OR FAILED — STOPPING
b3: BLOCK FAILED (post)
```

`run_case.sh` stopped (`RUN_CASE: STOP — post refused`, exit 4). `freeze_policy.py run-validity`
judged the run VALID (reasons [], `validity.json` written); the refusal is the next step,
`lanearchive.py extract`.

**Cause (reproduced, read-only).** Calling the `lanearchive` functions on the captured transcript
and state: `extract_lanes`, `peak_context` and `_state_codex` (status `joined`) succeed;
`locate_codex_dir` raises `ValueError("codex directory outside the temp root")`. The plugin's
Codex collector makes its dir with `mktemp -d "${TMPDIR:-/tmp}/vc-codex.XXXXXX"`. Inside the
measured session's sandbox, `TMPDIR` is Claude Code's sandbox temp dir, so the printed dir was
`/tmp/claude-501/vc-codex.AdNHkG` (`payload.json` present, `rc` = `0`). `lanearchive._temp_roots()`
accepts only the `post` process's own `tempfile.gettempdir()`
(`/private/var/folders/xq/…/T`), `/private/var/folders` and `/var/folders`. `/private/tmp/claude-501`
is outside them, so the safety check refuses. This happens for every Codex-joined run under the
S5/S6 containment, so no Codex-joined case can be archived: the sweep cannot complete on this
candidate. The containment proofs did not reach this step: `proof-verify` judges the proof
transcript, not the `post` lane archive.

**Not done (standing rule, D-23 / D-27).** No code change, no bypass, no hand-built archive. The
fix touches `plugins/vibe-check/scripts/lanearchive.py` (unmapped in PATH-MAP, so covered: a new
candidate) and possibly the runner layer. Candidate fix, not applied: accept the measured
session's sandbox temp root (for example the sandbox `TMPDIR` the session was given, recorded by
the runner) as a temp root in `locate_codex_dir`, with a test using the `/tmp/claude-<uid>/` shape
and a mutant showing it trips.

**The attempt (not a result).** `fail` moved the run to
`runs-phase54-live/attempts/live-reach-new-1-run-1-1792251211/` (state, stamps, `validity.json`
VALID, `tree.diff`, and the state file the run wrote; the transcript stays local and gitignored).
`lanearchive.py scan` on its committed files: clean. It is not counted as a result, not as a miss,
and not rerun; the slot stays open for the restart on a new candidate.

**Clean-up.** `/exit`, tmux session killed (no tmux server left). `revert reach-new-1`: triggarr
clone back on `main@4a154be`, status clean. The empty memory dir the session created (0 files) was
moved to the park dir as evidence; `restore-memory`: BLOCK OK. The empty `runs-phase54-live/reach-new-1/`
left by `fail` was removed (`rmdir`).

### Owner cache — after the stop (2026-10-17T15:33Z)

Fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3`, equal to the value
before. Owner config sha256 `962a26ec…`, `bf22ccb2…`, `012ecb8d…`, unchanged.

---

# Restart on candidate ddbfff402816 (54-11 restart #3)

Everything above this line is history and stays unchanged: the 302df48 attempt, the 24c0c00
sweep with its owner decision, and the 2a6dbb4 attempt that stopped at its first case (`post` lane
archive). Nothing from those counts on this candidate (D-21).

## Pre-registration — restart on candidate ddbfff4 — 2026-10-17T17:42Z (before the first run)

Since the 2a6dbb4 stop: follow-up 2d (bc5738e / 22ef678) made `lanearchive.locate_codex_dir`
accept the measured session's uid-scoped sandbox temp root `/tmp/claude-<uid>/`; follow-up 2e
(fd40e29 / ddbfff4) fixed the fix-harness turn-end classifier. 54-10 re-run #6 selected a new
candidate and regenerated the draft manifest.

- **Candidate:** `ddbfff402816805136e95393c98a3cc17196daeb`, read from
  `docs/design/freeze-v2.12/evidence/CANDIDATE.json` (never `HEAD`); it equals the draft
  manifest's `candidate_sha`.
- **Manifest:** `docs/design/freeze-v2.12/evidence/FREEZE-MANIFEST-draft-54-10.json`, `manifest_id`
  `fd1d0d916fe27de81f3c697673bbce65e6ab2c201a653e49875f0d6218cc81d3`, `MANIFEST` for the whole
  sweep. B3 launch model `claude-fable-5-1[1m]` (= `pin-model:`); plugin `runtime_fingerprint`
  `0ddf46f6…`. Pins unchanged: `claude --version` 2.1.281, `codex --version` 0.153.4 (checked
  live 2026-10-17T17:41Z).
- **Owner condition met before the sweep (S5–S7 synthetic live review):** the two 54-10 re-run #6
  containment proofs, both on this candidate and this manifest:
  - `evidence/containment-proof-b3.json` (479493f): CONTAINMENT PROOF OK. Python scoring ran,
    local gateway served the sessions, Codex joined (needs-attention); credential reads denied on
    Bash, Python, Node and the Read tool; unauthorized network denied (curl, Python, Node); env
    allowlist held. Its `archive_step_check` PASS: the review's Codex dir
    `/tmp/claude-501/vc-codex.O6m5rm` was archived by `lanearchive.py extract`, payload
    byte-identical — the step that stopped the 2a6dbb4 sweep.
  - `evidence/containment-proof-holdout.json` (ed3f9f8): CONTAINMENT PROOF OK, owner-run holdout
    review VALID (`run-validity` exit 0), `archive_step_check` PASS.
- **Invalid-run rule:** as the 2a6dbb4 pre-registration. Every run is judged by `post`'s
  `freeze_policy.py run-validity`; a permission failure, incomplete review or missing scorer output
  = INVALID, `fail`ed to `attempts/`, slot redone in a fresh run folder (next run number), never
  counted as quiet or a miss. An auth/API outage is an invalid environment attempt, recorded and
  redone the same way. A completed valid run is never rerun.
- **Infrastructure stop rule:** if any runner step breaks (as the archive step did), the sweep
  stops at that case and is reported; no code is changed.
- **Sandboxing is an environment change** (owner condition): this sweep can show outcome
  differences against the Phase-53 baseline and the 24c0c00 sweep; it cannot attribute any of them
  to the sandbox or rule it out.
- **Run folders:** the 2a6dbb4 attempt stays in `runs-phase54-live/attempts/` (not walked by
  `dev-tally`); the 24c0c00 runs stay in `runs-phase54-live/superseded-24c0c00038f2/`. New runs
  take `run-1`.
- **Clones:** re-used, each on its start branch and clean at 17:41Z: roonseek `2370f0b`,
  seedsyncarr `3dc75c7`, triggarr `4a154be`.
- **Everything else as before:** runner re-materialized from ddbfff4; memory parked; owner cache
  untouched; all 16 cases once, in the same order; no retune, no key change; fixed keystrokes;
  before = Phase-53 signed-off final run, with the 24c0c00 sweep shown for reference; lost-catch
  rule; the owner's R4 wording rules (2a6dbb4 pre-registration).

### Owner cache — before the sweep (2026-10-17T17:41Z)

Fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3` (unchanged).
Owner config sha256: `installed_plugins.json` `962a26ec…`, `known_marketplaces.json` `bf22ccb2…`,
`settings.json` `b5c6ac2e…` (changed since 15:33Z; the draft manifest was regenerated after it and
the identity check binds the effective settings).
