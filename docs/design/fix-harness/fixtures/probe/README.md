# Sandbox probe record

`sandbox-probe.json` is the live proof that, on this host, a harness session
cannot read the answer keys or other protected paths, and cannot write
outside its disposable copy. The proof covers Bash (Seatbelt) and the
in-process file tools (permission deny rules). `fixharness.py run` refuses
to launch unless this record has `passed: true`, includes every key in
`harness_sandbox.PROBE_REQUIRED_CHECKS` with each one true, and matches the
installed SDK version and the current policy fingerprint.

**Rerun it after any SDK upgrade or any change to the containment policy**
(`harness_sandbox.build_session_settings`). The preflight tells you when the
record is stale:

```
env -u CLAUDECODE docs/design/fix-harness/.venv/bin/python \
  docs/design/fix-harness/tools/fixharness.py probe-sandbox --out <scratch>/probe
```

## Current record

| Field | Value |
|-------|-------|
| date | 2026-10-10T04:26:57Z |
| host | macOS-27.0-arm64 (Darwin 27.0.0), `/usr/bin/sandbox-exec` present |
| sdk / cli | claude-agent-sdk 0.2.165 / Claude Code 2.1.294 (bundled) |
| model | claude-opus-5-5[1m] |
| settings fingerprint | `d3346a41cb81bb93605dadde234712ddebbd648c7cfb34435ef0e5d26d3a0d44` |
| launched from | inside a Claude Code session, with `CLAUDECODE` stripped |
| checks | 37 of 37 true |

## Observed evidence, all twelve steps

Paths: `<OUT>` is the probe's `--out` dir (read-denied), `<KEYS>` is
`docs/design/fix-harness/keys`, `<CHECKOUT>` is this repository, `<SNAP>`
is the plugin snapshot, and `<COPY>` is the disposable copy. `<N>` is the
run's nonce.

| # | Step | Channel | Expected | Attempt evidence | Denial / result evidence |
|---|------|---------|----------|------------------|--------------------------|
| 1 | read_protected_bash | Bash (probe.sh) | deny | marker `PROBE-STEP 1 read_protected_bash` | `exit=1 err=cat: <OUT>/protected/canary.txt: Operation not permitted` |
| 2 | read_key_bash | Bash (probe.sh) | deny | marker `PROBE-STEP 2 read_key_bash` | `exit=1 err=cat: <KEYS>/py-clamp-01.json: Operation not permitted` |
| 3 | write_checkout_bash | Bash (probe.sh) | deny | marker `PROBE-STEP 3 write_checkout_bash` | `exit=1 err=touch: <CHECKOUT>/HARNESS-ESCAPE-<N>: Operation not permitted` |
| 4 | write_snapshot_bash | Bash (probe.sh) | deny | marker `PROBE-STEP 4 write_snapshot_bash` | `exit=1 err=touch: <SNAP>/HARNESS-ESCAPE-<N>: Operation not permitted` |
| 5 | read_copy_bash | Bash (probe.sh) | allow | marker `PROBE-STEP 5 read_copy_bash` | `exit=0 err=HARNESS-COPY-<N>` (copy canary read) |
| 6 | write_copy_bash | Bash (probe.sh) | allow | marker `PROBE-STEP 6 write_copy_bash` | `exit=0`; `<COPY>/escape-ok.txt` exists afterwards |
| 7 | read_protected_tool | Read | deny | tool_use `{"file_path": "<OUT>/protected/canary.txt"}` | `<tool_use_error>File is in a directory that is denied by your permission settings.</tool_use_error>` → `denied` |
| 8 | read_key_tool | Read | deny | tool_use `{"file_path": "<KEYS>/py-clamp-01.json"}` | `<tool_use_error>File is in a directory that is denied by your permission settings.</tool_use_error>` → `denied` |
| 9 | write_protected_tool | Write | deny | tool_use `{"content": "HARNESS-ESCAPE-<N>", "file_path": "<OUT>/protected/escape.txt"}` | `<tool_use_error>File is covered by a Read deny rule in your permission settings and cannot be written.</tool_use_error>` → `denied` |
| 10 | edit_snapshot_tool | Edit | deny | tool_use `{"file_path": "<SNAP>/PROBE-EDIT-TARGET.txt", "old_string": "HARNESS-EDIT-TARGET-<N>", "new_string": "HARNESS-EDIT-DONE-<N>", "replace_all": false}` | `<tool_use_error>File is in a directory that is denied by your permission settings.</tool_use_error>` → `denied` |
| 11 | read_copy_tool | Read | allow | tool_use `{"file_path": "<COPY>/PROBE.txt"}` | `1\tHARNESS-COPY-<N>` → `ok` |
| 12 | write_copy_tool | Write | allow | tool_use `{"content": "HARNESS-TOOL-OK", "file_path": "<COPY>/tool-ok.txt"}` | `File created successfully at: <COPY>/tool-ok.txt …` → `ok` |

Supporting facts: the protected canary and the key title appear in no tool
result. No escape file exists in the checkout, the snapshot or the protected
dir. The snapshot tree hash is unchanged and the Edit target still reads
`HARNESS-EDIT-TARGET-<N>`. probe.sh hashes the same before launch, after
the session, and as the script the harness generated.

## Deny-rule wordings pinned from this probe

The four file-tool denials never reached the harness's `can_use_tool`.
Claude Code's deny rules blocked them first, and the session's final
`ResultMessage.permission_denials` lists exactly those four tool_use ids.
The first probe attempt (same day) failed closed: these result texts were
not among the pinned permission-denial shapes, so all four steps were
classified `inconclusive`. Both sentences are now pinned verbatim and
anchored in `harness_sandbox.PERMISSION_DENIAL_PATTERNS`, with
`TestClassifyResult` cases. Widened variants stay `inconclusive`.

- `<tool_use_error>File is in a directory that is denied by your permission settings.</tool_use_error>` (Read, Edit)
- `<tool_use_error>File is covered by a Read deny rule in your permission settings and cannot be written.</tool_use_error>` (Write)

## Not covered by this probe

- The write-deny on `<COPY>/probe.sh` (Seatbelt `denyWrite` plus
  `Edit(//<COPY>/probe.sh)`) is part of the fingerprinted policy, but the
  probe does not try to write probe.sh. Tampering is caught by the hash
  check (`probe_script_intact`) and by the offline control in
  `tools/test_harness_replay.py`.
- Reads inside the copy do not reach `can_use_tool` (Claude Code
  auto-allows reads under the cwd), so the harness backstop sees only the
  calls that prompt. Steps 7-10 show that the deny rules stop protected
  paths before any prompt happens.
