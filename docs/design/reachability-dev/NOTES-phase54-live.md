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

AXIS: <credit | no credit> — row <stable_hash[:12]> (<alarm | needs-verification>) — <reason against the keyed defect>

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

AXIS: <credit | no credit> — row <stable_hash[:12]> (<alarm | needs-verification>) — <reason against the keyed defect>

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

AXIS: <credit | no credit> — row <stable_hash[:12]> (<alarm | needs-verification>) — <reason against the keyed defect>

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

AXIS: <credit | no credit> — row <stable_hash[:12]> (<alarm | needs-verification>) — <reason against the keyed defect>

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
