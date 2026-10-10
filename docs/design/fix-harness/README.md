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

## Running

One command per run (the CLI entry point is `tools/fixharness.py`):

```
python3 tools/fixharness.py run --case py-clamp-01 --mode default --out runs/<run-id>
```

The SDK lives in a harness-only venv:

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Unit tests are stdlib-only and run with bare `pytest -q` from `tools/`.

## Isolation rules

- Cases are synthetic. Never build a case from the B3 benchmark diffs or the
  holdout set, and never read those inputs from harness code.
- Answer keys never enter the copy. The copy builder copies only a case's
  `base/` (and `gsd/` in GSD layout) plus the defect file; `keys/`,
  `recipe.json` and the defect check stay outside the run.
- After launch, every state change in the copy comes through the plugin. The
  harness seeds state and plants sentinels before launch and only reads the
  copy afterwards.

## Timing labels

Each run record reports the automated execution time and the harness's own
answer time. Time spent waiting on the owner is not measured in a scripted run:
it is recorded as `null` with the note "not measured — scripted run, no human
in the loop", never as zero.
