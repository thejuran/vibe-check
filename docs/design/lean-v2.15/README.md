# v2.15 lean-orchestration kit

This folder holds the 2.14.1 baseline that the v2.15 work is compared with, the rule for judging
whether that work is an improvement, and the small standard-library tools that make and re-check
the records. Nothing here changes the plugin; every tool reads the pinned commit or recorded files
and writes only to the path it is given.

| Tool | Job |
|------|-----|
| `step_count.py` | counts the mechanical steps the model carries out on a mode path (bash blocks, inline commands, Write-tool writes, values copied between commands) at a revision or a folder (`--rev` or `--root`, `--mode`, `--json`, `--out`) |
| `finalize_capture.py` | walks the five Finalize situations offline at the pinned commit and records what they produce (`capture`), or compares a fresh walk with the committed record (`verify --repo <root> --record <json>`); `compare --repo <root> --record <json> --driver helper` (`--commit <sha>` or `--root <plugin dir>`) walks the same five situations on a later version's instructions and passes only when the outcome fields match the record, listing the changed lists of commands run as the intended difference |
| `path_records.py` | records declared bytes per mode path (`footprint`) and the files recorded sessions actually opened (`traces`), and re-checks both (`verify`, `verify-traces`) |
| `usage_fields.py` | read-only reader of the usage fields in recorded sessions: field names, counts and token sums, never prices (`--session`, `--archive-root`, `--json`), and a price and private-path check for a written note (`check-note`) |
| `baseline_records.py` | captures the replay report (`capture-replay`), writes the suite record (`suite-record`) and the manifest (`manifest`), and re-checks the whole baseline in one command (`verify --repo <root>`, which prints `baseline holds`) |

Each tool has a `test_<name>.py` beside it. `test_baseline_page.py` keeps every figure on
`BASELINE-v2.14.1.md` equal to the records and keeps this table complete.

## Layout

- `baseline/` — the committed 2.14.1 records (suite, replay reports and fingerprints, the five
  Finalize situations, bytes per path, loaded-file traces, step counts) and `MANIFEST.json`, which
  fingerprints every file in the folder. Do not edit these by hand.
- `CRITERION.md` — the improvement rule and comparison workload for the Finalize slice.
- `BASELINE-v2.14.1.md` — the plain-terms summary of the baseline, numbers first.
- `tools/` — the tools above and their tests.
