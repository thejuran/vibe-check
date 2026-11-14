---
phase: 62-baseline-and-continuous-test-run
plan: 05
subsystem: baseline-evidence
tags: [BASE-02, footprint, traces, privacy-lock]
requires: []
provides:
  - docs/design/lean-v2.15/baseline/footprint-v2.14.1.json (declared mode-path bytes at dd8e4ab)
  - docs/design/lean-v2.15/baseline/traces-v2.14.1.json (labelled loaded-file traces)
  - docs/design/lean-v2.15/tools/path_records.py (footprint / traces / verify / verify-traces)
affects: [Phase 63 Finalize byte comparison, Phase 65 no-growth proof for plain and deep review]
tech-stack:
  added: []
  patterns: [git-show recount at pinned commit, capture-time agreement guard, never-echo privacy lock with planted mutants]
key-files:
  created:
    - docs/design/lean-v2.15/tools/path_records.py
    - docs/design/lean-v2.15/tools/test_path_records.py
    - docs/design/lean-v2.15/baseline/footprint-v2.14.1.json
    - docs/design/lean-v2.15/baseline/traces-v2.14.1.json
  modified: []
decisions:
  - "Standing check reads the declared file lists from footprint.py AS IT STOOD at dd8e4ab (git show), so later edits to footprint.py cannot break or silently move the 2.14.1 record"
  - "Each observed path entry carries label 'observed'; a 'declared, not observed' path always carries a gap sentence; a listed-but-absent session is named by prefix in gap with no stand-in"
  - "Problem lines never echo a recorded value that fails the plugin-relative check; private-content problems name the JSON location only"
metrics:
  completed: 2026-11-14
  tasks: 2
  files: 4
---

# Phase 62 Plan 05: Mode-path bytes and loaded-file traces at 2.14.1 Summary

Declared per-mode-path byte record at v2.14.1 (re-derived from `git show dd8e4ab` on every test run, token proxies held in their own labelled block) plus labelled loaded-file traces from the five recorded smoke sessions, with deep review recorded as `declared, not observed`, all guarded by a privacy lock that is shown to trip on planted mutants.

## What was recorded

**Footprint (declared, bytes at `dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4`)** — matches the pinned figures exactly; nothing was edited:

| Mode | Label | Bytes | Files |
|---|---|---|---|
| review-plain | plain review | 192,057 | 13 |
| deep-plain | deep review | 268,997 | 19 |
| finalize | Finalize | 136,114 | 7 |
| review-all / deep-all / fix-loop | — | 284,926 / 361,866 / 255,070 | 20 / 26 / 14 |

Token figures appear only under `proxies` (label `PROXY — derived from bytes, not measured, not a bill`). No price figure anywhere. Word counts from the decoded-text split agree with footprint.py for every file.

**Traces (names and aggregates only):**

| Path | Label | Sessions | What the declared list misses |
|---|---|---|---|
| Finalize | observed | `b1bb3036` (2.14.0 candidate 0d2be77, smoke) — Read 9, Bash 12, Write 4 | `templates/review-md-schema.md` (5,035 B) |
| plain review | observed | `5caa5cec`, `15a3be6d` (2.14.0 cand., smoke); `b0294925`, `6a70827e` (2.14.1, smoke) | `phases/review/50-fix-loop.md` (63,013 B, all four, fix loop entered); `templates/output-format.md` (14,226 B, three of four) |
| deep review | declared, not observed | none | gap: no recorded 2.14.x session; nothing run to fill it (D-09) |

`verify-traces` re-extracted all five sessions on this machine and the record held (exit 0). All five listed session files were present; no stand-in was used.

## Verification actually run

- `pytest -q -p no:cacheprovider docs/design/lean-v2.15/tools/test_path_records.py` → **59 passed, 0 failed**.
- Task 1 JSON assertions (pinned totals, no `token` in `paths`, `PROXY` label, no `$`) → passed.
- `path_records.py verify --repo . --footprint … --traces …` → exit 0 (`records hold`).
- Plan's planted-path break test (gap set to `see /Users/x/notes/secret.md`) → verify exited non-zero, `break-test-ok`.
- `grep -cE '/Users/|/private/|/home/'` on the traces record → 0; longest line 113 chars. I read the written record's contents myself (names, counts, bytes, labels only).
- `git status --porcelain` after each task showed only this plan's four files; nothing under `plugins/` changed.
- RED commits observed failing before GREEN: Task 1 RED failed on the missing module (collection error); Task 2 RED had 39 failing.

Mutants that were run and tripped: three footprint tamper mutants and the capture-guard mutant (`path_stats` +1 byte → `FOOTPRINT RECOUNT DISAGREES WITH footprint.py — STOPPING`, exit 1, no file); five traces tamper mutants; planted private path, 201-char string, full 36-char session id (each reported; 200-char boundary not reported); lock patched off → both plants no longer reported; read filter patched off → synthetic-session test raises AssertionError; `traces` with a forced private path → `TRACES RECORD HOLDS PRIVATE CONTENT — STOPPING`, exit 1, no file.

## Deviations from Plan

### Auto-fixed / design calls

**1. [Rule 2 - Correctness] Standing check takes declared lists from footprint.py at the pinned commit**
- **Found during:** Task 1
- **Issue:** The plan says the standing test must stay valid when a later phase edits footprint.py, but a "file removed from a mode's list" tamper must name the missing file, which needs the declared list from somewhere independent of the live module.
- **Fix:** `baseline_mode_paths` reads `scripts/footprint.py` from `git show <commit>` and evaluates it with a non-main `__name__` to get MODE_PATHS as of 2.14.1. Capture still checks against the live `footprint.path_stats`.
- **Cost if wrong:** if footprint.py at the pinned commit ever stopped being exec-safe, `verify` would report "footprint.py absent/no MODE_PATHS" instead of passing; a fix is a frozen copy of the lists.
- **Commit:** 325ea82

**2. [Rule 2 - Security] Problem lines never echo non-plugin values**
- **Found during:** Task 2
- **Issue:** A planted `/Users/…` read path would otherwise be echoed by the byte or declared-list problem lines.
- **Fix:** `_show()` replaces any non-plugin-relative recorded path with `<not a plugin-relative path>`; private-content problems give the JSON location only; tests assert `/Users/x` is absent from CLI output.
- **Commit:** 468846b

**3. Small additions beyond the behaviour list**
- `--commit` on `footprint`/`traces`; `verify-traces --repo` defaults to the repo holding the script.
- Each read carries `at_baseline: present|absent`; each observed entry carries `malformed_lines` (count only, T-62-26).
- `traces` also runs `verify_traces_record` before writing (`TRACES RECORD FAILS ITS OWN CHECK — STOPPING`); `verify` cross-checks each traces `declared` list against the footprint record.
- `kind` is stored as the mode key (`finalize`, `review-plain`); the human label lives in the footprint record's `label`.
- **Cost if wrong:** cosmetic; consumers in Phases 63/65 read `paths.<mode>`.

## Assumption Drift (advisory)

- **Found during:** Task 2. **Planned:** `smoke_session: true` for the listed sessions. **Actual:** derived at source from the version label containing `smoke session` (all five labels do). **Why:** keeps the flag tied to the label the owner sees. **Cost if wrong:** a future non-smoke session labelled with that text would be flagged smoke; low.

## Known Stubs

None.

## Threat Flags

None. Threats T-62-22 through T-62-26 are mitigated as planned (synthetic fixtures only, privacy lock wired into `verify` and `traces`, session hash binding, git recount, malformed lines counted by `tracecheck.events`).

## Self-Check: PASSED

- FOUND: docs/design/lean-v2.15/tools/path_records.py
- FOUND: docs/design/lean-v2.15/tools/test_path_records.py
- FOUND: docs/design/lean-v2.15/baseline/footprint-v2.14.1.json
- FOUND: docs/design/lean-v2.15/baseline/traces-v2.14.1.json
- FOUND commits: 6ca6a03, 325ea82, e4c97c9, 468846b
