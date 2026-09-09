# Batch lifecycle — v2.10 Phase 40

**Purpose:** build, run against, judge, advance past, or roll back any Phase-40 restructure batch
from one page, with every step mechanically checkable.

Every step below is one `batchsnap.py` subcommand. This doc is the LIFECYCLE only — which diffs to
run, which commands to type inside a run, and how results are scored live in
`SPOT-CHECK-v2.10-phase40.md` (plan 40-09). The MEASUREMENT-RUN RULE and the per-run archive block
live in `RUN-CHECKLIST-v2.10.md` §"MEASUREMENT-RUN RULE" and are NOT duplicated here.

`batchsnap.py` lives at `plugins/vibe-check/scripts/batchsnap.py`.

---

## 1. What a batch is

| Batch | Plans | Rollback unit? | Owner check |
|---|---|---|---|
| — (evidence) | 40-01 | **NO — outside every unit** | none |
| 1 | 40-02, 40-03, 40-04, 40-05, 40-07, 40-12, 40-13 | yes | 2 runs |
| 2 | 40-08, 40-10 | yes | 2 runs |
| 3 | 40-11 | yes | 2 runs |
| end-of-phase | — | — | 6 runs (2 diffs ×3) |

**40-01 is outside every rollback unit**, for two structural reasons: reverting the verifier would
add a third commit to a path whose own new gate requires exactly two, and a ledger that can be
un-appended is not append-only.

**40-06 and 40-09 are also outside every rollback unit.** They are the lifecycle tooling and the
owner run checklist; reverting the tooling while trying to use it to revert something is
self-defeating. 40-14 (the closing record) is excluded for the same class of reason.

### How the exclusion is enforced

Membership comes from `BATCH_PLANS`, an explicit per-batch ALLOWLIST of plan ids, resolved against
`PLAN-COMMITS.json` — the file each plan appends its own commit sha to via
`batchsnap.py record-commit`. Recording is a write performed by the plan that made the commit,
because that plan is the only thing that knows its own identity. **Selection never inspects commit
subjects.** 40-01's commit subject carries no plan tag and it touches a file under
`plugins/vibe-check/`, so any subject-or-path heuristic would have swept it into batch 1's revert
set and destroyed the append-only ledger.

`NEVER_REVERT` (`40-01`, `40-06`, `40-09`, `40-14`) is asserted INSIDE `commit_set`, so a mistake in
the allowlist fails the command instead of silently reverting evidence.

---

## 2. Build the snapshot (assistant does this at batch close)

First confirm every plan in the batch recorded its commit. This exits 1 naming any plan that did
not:

```bash
set -euo pipefail
cd <repo>
python3 plugins/vibe-check/scripts/batchsnap.py commit-set --batch <N> \
  --recorded docs/design/b3-ground-truth/runs-v2.10-phase40/PLAN-COMMITS.json \
  || { echo 'BATCH INCOMPLETE OR ALLOWLIST WRONG — STOPPING'; exit 1; }
```

Then build:

```bash
set -euo pipefail
cd <repo>
python3 plugins/vibe-check/scripts/batchsnap.py build --batch <N> \
  --commit "$(git rev-parse HEAD)" \
  --recorded docs/design/b3-ground-truth/runs-v2.10-phase40/PLAN-COMMITS.json \
  || { echo 'SNAPSHOT BUILD REFUSED — STOPPING'; exit 1; }
```

Record BOTH printed roots and the printed commit set in the batch's `PASS.json` skeleton.

`build` REFUSES — an incomplete batch cannot be handed to the owner — if any of these hold:

- the working tree is dirty under `plugins/vibe-check` (the batch is not actually complete there);
- any lazy-read instruction points at a file that does not exist in the snapshot;
- the plugin has a `phases/` directory but zero lazy-read instructions reference it;
- `plugin_root/.claude-plugin/plugin.json` is absent;
- the suite is not green inside the snapshot;
- the sealed archive tree does not match the pin `82c412b6e58b5d5a1dbddca0239f0f4b26833b4a`.

Sealing is the LAST action: the completeness check, the suite, and the commit-set resolution all
run BEFORE anything is hashed, so the manifest describes the tree's final state. Generated files
(`__pycache__/`, `*.pyc`, `.pytest_cache/`) are excluded from the hash set, and that exclusion list
is recorded inside the manifest so `verify` judges the snapshot by the rules its own build used.

---

## 3. Run against the snapshot (owner)

**The two roots are different paths and only one of them is the launch argument.**

- `SNAP_ROOT` — what `build` printed as `snapshot_root:`. A full-repo worktree.
- `PLUGIN_ROOT` — what `build` printed as `plugin_root:`. Equal to
  `$SNAP_ROOT/plugins/vibe-check`, and the place `.claude-plugin/plugin.json` actually lives.

Before EVERY single run:

```bash
set -euo pipefail
SNAP_ROOT=<the snapshot_root build printed>
python3 <repo>/plugins/vibe-check/scripts/batchsnap.py verify --snap "$SNAP_ROOT" \
  || { echo 'SNAPSHOT CHANGED UNDER YOU — STOPPING'; exit 1; }
PLUGIN_ROOT=$(python3 <repo>/plugins/vibe-check/scripts/batchsnap.py verify --snap "$SNAP_ROOT" \
  | tail -1 | sed 's/^plugin_root: //')
test -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" \
  || { echo 'NO PLUGIN MANIFEST AT PLUGIN_ROOT — STOPPING'; exit 1; }
```

`verify`'s last line is `plugin_root: <path>`, so the launch argument is always taken from a
just-verified snapshot rather than retyped. Then the ONE launch line:

```bash
cd <source repo clone> && claude --plugin-dir "$PLUGIN_ROOT"
```

**Never pass `--plugin-dir` pointing at the working repo during a batch check.** The working tree is
mutable and phase files are read LAZILY, minutes into a session — a clean-tree check at launch
proves nothing, because the assistant may be mid-edit when the session actually reads the file.

**Never pass `--plugin-dir "$SNAP_ROOT"`.** The repo root holds no plugin manifest, so the run would
silently fall back to the installed cache and measure the wrong plugin entirely — an unrelated
measurement that looks exactly like a real one.

---

## 4. Provenance check after each run

The run's transcript is captured per plan 40-09. Confirm the helper and agent paths appearing in it
are under `$PLUGIN_ROOT` — not under the working repo, and not under the installed cache. This is
also the check that catches a run accidentally launched with `$SNAP_ROOT`:

```bash
set -euo pipefail
grep -nE '(turingmind-code-review/plugins/vibe-check|plugins/cache/)' <transcript> \
  && { echo 'RUN TOUCHED A NON-SNAPSHOT PLUGIN PATH — RUN IS VOID, STOPPING'; exit 1; }
echo 'provenance clean'
```

A match means the run exercised something outside the snapshot; discard it and re-run after
re-verifying. Isolation is checked here, not assumed.

---

## 5. Record the verdict

The owner fills the MECHANICAL fields only — `diff`, `run_index`, `state_shape`,
`tree_diff_sha_match`, `report_path`, `transcript_path`, `trace_validation` — and leaves
`adjudication` at `"pending-assistant"`. The assistant adjudicates SITE/AXIS/BAND afterwards and
commits the completed artifact. A barrier REFUSES an artifact still carrying `pending-assistant`,
so the handoff cannot be skipped.

Written to `docs/design/b3-ground-truth/runs-v2.10-phase40/batch<N>/PASS.json`:

```json
{
  "batch": 1,
  "snapshot_commit": "<the snapshot_commit build printed>",
  "verdict": "PASS",
  "recorded_by": "owner",
  "recorded_at": "2026-09-08T12:00:00Z",
  "runs": [
    {
      "diff": "should-catch-3",
      "run_index": 1,
      "state_shape": "PASS",
      "tree_diff_sha_match": true,
      "report_path": "run1/report.md",
      "transcript_path": "run1/transcript.jsonl",
      "trace_validation": "not-applicable",
      "adjudication": "pending-assistant"
    },
    {
      "diff": "should-quiet-2",
      "run_index": 1,
      "state_shape": "PASS",
      "tree_diff_sha_match": true,
      "report_path": "run2/report.md",
      "transcript_path": "run2/transcript.jsonl",
      "trace_validation": "not-applicable",
      "adjudication": "pending-assistant"
    }
  ]
}
```

A `verdict` of `"PASS"` is not certifiable from key presence. `check-pass` additionally requires
every run's `state_shape` to be `PASS`, `tree_diff_sha_match` to be boolean `true`,
`trace_validation` not to be `fail`, `(diff, run_index)` to be unique, and both captured artifacts
to EXIST on disk beside the artifact. A run recording a mechanical failure forces the batch's
verdict to `FAIL`.

---

## 6. Advance

The next batch's FIRST task is a barrier that consumes the prior batch's evidence:

```bash
set -euo pipefail
python3 plugins/vibe-check/scripts/batchsnap.py check-pass \
  --file docs/design/b3-ground-truth/runs-v2.10-phase40/batch<N>/PASS.json \
  || { echo 'PRIOR BATCH NOT VALIDATED — STOPPING'; exit 1; }
```

It halts on absence, malformation, or a FAIL. Three plans carry a barrier:

- **40-08** — barrier for batch 1
- **40-11** — barrier for batch 2
- **40-14** — barrier for batch 3 and the end-of-phase check

---

## 7. Revert

1. `git revert --no-commit <sha>` for each sha in the batch's recorded `commit_set`, **in the
   printed order** (it is already newest-first, i.e. reverse-order revert), then ONE commit:
   `revert(40): batch <N> rolled back after a failed live check`.

2. **Dependent batches.** If a later batch has already landed, revert the LATER batch first, then
   this one — the same reverse-order rule applied across batches. Concretely: to roll back batch 2
   when batch 3 has landed, revert batch 3's set, then batch 2's set. If the later batch must be
   kept, do NOT hand-edit: revert both and re-land the later batch's plans on the corrected base.
   Partial rollback by hand is how a plugin ends up in a state no snapshot describes.

3. **Never revert:** 40-01's commits, 40-06's and 40-09's tooling commits, and anything under
   `docs/design/b3-ground-truth/`. The archives and the ledger are evidence; a failed live check
   does not invalidate evidence.

4. **After any revert:** rebuild the snapshot at the new HEAD, which re-runs the completeness, suite
   and archive-tree checks, then re-run the batch's 2 checks against the NEW snapshot. A revert is
   not complete until a snapshot builds and passes on top of it.

```bash
set -euo pipefail
cd <repo>
for sha in $(python3 plugins/vibe-check/scripts/batchsnap.py commit-set --batch <N> \
    --recorded docs/design/b3-ground-truth/runs-v2.10-phase40/PLAN-COMMITS.json); do
  git revert --no-commit "$sha" || { echo 'REVERT CONFLICT — STOPPING'; exit 1; }
done
git commit -m "revert(40): batch <N> rolled back after a failed live check"
```

---

## 8. What a FAIL means

A failed live check reverts the BATCH. It does not revert evidence, does not revert tooling, and
does not change the sealed baseline.

Record the FAIL in the batch's `PASS.json` with `"verdict": "FAIL"` and KEEP it. The artifact is the
audit trail either way — a batch that failed and was rolled back is a recorded result, not an
absence.
