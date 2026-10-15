# v2.12 freeze kit

The freeze kit pins the exact release candidate the v2.12 measurements run
against, stops any run whose environment differs from it, and decides which
results may count toward a release gate. Four tools live in `tools/`:

| Tool | Job |
|------|-----|
| `freeze_manifest.py` | builds `FREEZE-MANIFEST-<N>.json` from a candidate commit (`generate`, `show`, `verify-self`) |
| `freeze_check.py` | the pre-run identity check (`verify --runner <r>`) and the candidate guard (`candidate-guard`) |
| `freeze_policy.py` | path classification, eligibility, inheritance, slot-based gate status, the retune seal-order proof (`classify`, `seal-order-proof`) |
| `freeze_tally.py` | the one entry point in front of every tally (`list`, `b3-aggregate`, `dev-tally`, `harness-verdicts`, `gate`) |

`PATH-MAP.json` maps changed paths to the checks they require. `evidence/`
holds gate evidence and proofs; it is reporting-only and never moves the
candidate.

## What is frozen

A manifest records the candidate by content, never by version string or
mtime:

- **Candidate:** `candidate_sha` (40-hex) and its tree. The candidate is the
  commit the manifest describes; the manifest itself is committed later as
  a descendant, and it is excluded from its own hash (no circular
  dependency). `evidence/CANDIDATE.json` carries the candidate SHA forward.
- **Plugin:** every file under `plugins/vibe-check` with its sha256 and
  mode, the tree hash, the runtime fingerprint score43 computes, and the
  plugin.json version (context only).
- **Covered artifacts outside the plugin:** every runtime-consumed
  instruction, configuration file, fixture and script the reviewers,
  runners or gate tooling load, including Markdown: the fix-harness tools,
  fixtures, keys and requirements; the holdout kit tools; this kit's tools,
  PATH-MAP.json and this README; the B3 runner and the live-check runbook
  whose blocks it executes (`reachability-dev/RUN-PHASE54-live.md`), the
  Phase-53 runbook carrying the verdict rules it points to, the
  reachability README approval record (`check_case`), the keyed catch
  sites (`CATCH-SITES-dev.json`) and the B3 case diffs
  (`b3-ground-truth/diffs`); the reachability cases; the
  B3 answer keys, catch manifests, supersessions, allowances and
  calibration notes.
- **Models:** agent pins, the top-level routing and its source, per-call
  overrides, the launch model per runner.
- **Codex:** CLI version, the model / effort / service-tier projection of
  `config.toml` plus a whole-file hash, the companion plugin identity.
- **Runner profiles:** one per runner (B3, fix harness, holdout autopilot,
  holdout measurement launcher): CLI version and binary hash, the
  user-level identity set (global instructions, hooks and their scripts,
  permissions, enabled plugins with content identities, allowlisted env,
  effort and model settings), the runner settings template, update pins.
- **Lineage:** the previous manifest's id and candidate, or null for the
  first manifest in the series.

Secrets never enter a manifest: a closed schema refuses any secret-shaped
value by dotted path without echoing it.

The kit lives outside `plugins/` on purpose. Nothing here ships with the
plugin, so the kit never enters the plugin file set it hashes.

## Runner contract

Every runner calls the identity check before EVERY run, including retries
and resumed runs:

```
python3 docs/design/freeze-v2.12/tools/freeze_check.py verify --runner <runner> ...
```

- A mismatch stops before launch, naming each exact difference. There is no
  override flag. The remedy is to fix the install, or to issue a new
  manifest after the checks the change requires.
- Every result stores the three stamp lines the check prints:
  `manifest_id:`, `check_digest:`, `candidate_sha:`. A result without them
  is never eligible.
- Every runner materializes its plugin copy from the candidate commit via
  git (`git archive` or a worktree at the candidate), never from the
  working tree.
- Runner settings pin `DISABLE_AUTOUPDATER=1` and `DISABLE_UPDATES=1`. A
  Claude Code or Codex CLI version change stops before the next run.
  Restoring the pinned version resumes under the same manifest; adopting a
  new version needs a new manifest and the reruns it requires.

**Runner-input binding table.** Every input a runner consumes at launch from
an installed or home location is bound by the check:

| Runner | Inputs consumed at launch | How the check binds them |
|--------|---------------------------|--------------------------|
| B3 | `$RUNNER_SETTINGS` passed to `claude --settings`; `~/.claude` user level; native CLI; Codex `config.toml` and companion | the SAME `$RUNNER_SETTINGS` path is given to `verify --settings` and compared by content after the single `<RUNNER>` statusLine substitution; user-level projection; CLI version + binary sha256; `config.toml` whole-file hash + companion tree |
| Holdout measurement launcher | the settings file it materializes from the candidate template; user level; native CLI | the same path goes to `verify` and to the spawn argv; user-level projection; CLI version + binary |
| Fix harness | inline `build_session_settings`; inherited process env; launch model; Agent SDK and its bundled CLI | settings fingerprint vs the committed probe record (in the hashed kit tree); allowlisted env projection; explicit `launch_model`; SDK version + bundled CLI version and binary |
| Holdout autopilot | no plugin; kit tree; native CLI | kit tree hash; CLI version + binary |

Nothing a session loads is left unbound.

### Engineering evidence records

The three engineering records are the ONE place these shapes are stated.
The test, security and deep-review release steps write them under
`evidence/`. `freeze_tally.py gate --gate engineering --runs-root evidence/`
reads them.

They are written BEFORE the manifest exists (D-23: gates run on the
finished candidate, then the manifest is generated from it). They therefore
carry NO `manifest_id` and NO `check_digest`. The policy binds them by
candidate instead: `freeze_policy.engineering_record_bound` requires
`candidate_sha` equal to the active manifest's `candidate_sha`, never a
manifest id.

The policy reads only three fields; every other key is opaque to it:

- `candidate_sha`: 40-hex, the candidate the step ran on.
- `candidate_guard`: the `freeze_check.py candidate-guard` output line,
  beginning `CANDIDATE OK`.
- `outcome`: `pass` is the only passing value.

Full key lists each writer produces:

- `evidence/test-gate.json`: `candidate_sha`, `head_sha`,
  `candidate_guard`, `ran_at`, `suites` (each: `name`, `workdir`, `command`,
  `passed`, `failed`, `duration_s`, `python`, `pytest`), `outcome`
  (`pass` | `fail`).
- `evidence/security-gate.json`: `candidate_sha`, `head_sha`,
  `candidate_guard`, `range`, `versions`, `halves`, `coverage`, `replica`,
  `triage`, `outcome` (`pass` | `fail`), optional `reasons`.
- `evidence/deep-review-release.json`: `candidate_sha`, `head_sha`,
  `candidate_guard`, `reviewer_build_fingerprint`, `reviewer_cache_path`,
  `delta_range`, `integration_range`, `lanes_delta`, `lanes_integration`,
  `state_paths`, `findings`, `critical_count`, `warning_count`,
  `medium_count`, `outcome` (`pass` | `blocked`).

A record naming any other commit is ineligible (`candidate mismatch`). A
record whose `outcome` is not `pass` fails its slot.

## Post-freeze change policy

Every change after the freeze is classified by changed path against
`PATH-MAP.json`. Requirements COMBINE: a path's categories are the union
over every matching rule, never a single "strictest" category.

| Category | Required checks |
|----------|-----------------|
| engineering | tests + security scan + deep review of the change |
| detection | B3 x3 + holdout x3 |
| workflow | 16 preservation + 2 clean-tree accepted-fix runs |
| reporting | no rerun; the identity check must still pass |

- An unmapped path requires every rerun set, including engineering.
- Shared helpers and configuration map to every workflow they affect.
- A change to `PATH-MAP.json` is classified under BOTH the map pinned at
  the candidate and the new map (union), and the map file itself always
  requires every rerun set, so a map edit can never reduce its own checks.
- Any proposed reduction (a rule whose categories shrink or vanish, a new
  rule that narrows the unmapped fallback) prints `needs owner approval`
  and is never applied automatically.

Commands:

```
python3 docs/design/freeze-v2.12/tools/freeze_policy.py classify --candidate <C>
python3 docs/design/freeze-v2.12/tools/freeze_tally.py gate --gate <gate> --runs-root <R>
```

## Inheritance and lineage

Each result keeps the identity of the manifest it ran under. A new manifest
may inherit a gate's results only when BOTH hold:

- the classification of the commit range previous candidate -> new
  candidate leaves the gate's category untouched; and
- every gate-relevant manifest field is present and equal in both
  manifests: for B3 and holdout, the plugin tree, models, Codex, and the
  runner's CLI, user level and launch model; for the workflow gate, the
  plugin tree, the fix-harness runner profile and the covered fix-harness
  tree.

A missing or ambiguous field, or a previous manifest that cannot be found
in the series, means rerun. Engineering never inherits across candidates:
its records are bound to one candidate SHA. RESULTS shows which manifest
each gate ran on.

## Reporting-only commits

Commits that touch only reporting paths (RESULTS, the top-level README and
CHANGELOG, evidence, run logs, planning notes) need no new manifest,
provided the identity check confirms every covered artifact is unchanged.
`freeze_check.py candidate-guard` enforces this. The frozen candidate SHA
stays as provenance; later doc commits are recorded separately.

The exemption is narrow. Instructions, configuration, fixtures or scripts
consumed by reviewers, runners or gate tooling stay covered, even when they
are Markdown. `plugins/vibe-check/README.md` is part of the hashed plugin
tree. A change to it is classified reporting, but it needs a NEW manifest:
the identity check will not pass silently. Every measurement gate inherits
across that manifest, because the only differing file is reporting-only.

## Evidence rules

- Failed and superseded runs stay on disk, labeled. They are never
  deleted, and never satisfy a passing gate.
- Missing or failed mandatory evidence = UNMET. An owner waiver may
  authorize shipping, but it is never MET: `gate_status` has no waiver
  input and never converts UNMET to MET.
- Prerequisites are candidate-bound. `freeze_tally.py gate` loads
  `test-gate.json`, `security-gate.json` and `deep-review-release.json`
  from `evidence/`. Each must name the active manifest's `candidate_sha`
  with `outcome: pass` (see the engineering evidence record contract
  above). For a manifest with lineage, the previous manifest must resolve
  in the series and any owed seal-order proof must exist and validate.
  Otherwise every gate is UNMET, with the prerequisite named.
- The candidate SHA comes from `evidence/CANDIDATE.json`. Later commits are
  checked with `freeze_check.py candidate-guard`: HEAD descends from the
  candidate, every later change is reporting-only, and every covered
  artifact is equal. The check is never `HEAD == candidate`.
- Gates are SLOT-based, never count-based. A slot is filled by exactly one
  eligible passing record. Repetitions of one case never fill another slot.
  Two eligible records for one slot are a duplicate, which is UNMET.
  Extras (a fourth run, an unknown case) are listed and never count.

| Gate | Mandatory slots | Rule |
|------|-----------------|------|
| `b3x3` | 36: 12 diffs x runs 1-3 | catch 15/15; false alarms <= 3 over the 18 counted quiet slots (`should-quiet-7` excluded) |
| `holdoutx3` | 18: 6 roster case ids x runs 1-3 | per case: each catch case caught >= 2/3, each quiet case fired <= 1/3; never aggregated |
| `workflow` | 16 preservation ((5 B3 should-catch diffs + 3 holdout catch ids) x {default, gsd}) + 2 clean-tree ({default, gsd}) | every filled run `COMPLETE` |
| `engineering` | 3: tests, security, deep-review | `engineering_record_bound` |

The holdout roster (`{schema: holdout-roster/1, cases: {id: catch|quiet}}`,
3 + 3 opaque ids) comes from the holdout kit at unseal time. Phase 55
harness `--case` ids MUST be the B3 diff names and holdout case ids, so that
`run.json` `case_id` fills its slot. The holdout launcher's `identity.json`
carries `case_id` and `run_name`.

## Retune

A detection change after a measurement requires fresh holdout replacements
sealed BEFORE the repair. The proof is versioned:
`evidence/seal-order-<new manifest_id first 12>.json`, schema
`freeze-seal-order/1`, with `previous_candidate_sha`, `retired_case_ids`,
`replacement_case_ids` (opaque ids only), `replacement_seal_commit` and
`first_repair_commit`. Only this command writes it:

```
python3 docs/design/freeze-v2.12/tools/freeze_policy.py seal-order-proof --manifest <M> --previous-manifest <P> --seal-commit <S> --retired <id>... --replacement <id>...
```

It is validated by git ancestry, in this sequence:

1. Previous candidate.
2. The owner removes the committed seal with
   `git rm docs/design/holdout-v2.12/SEAL.json` and a commit naming the
   retired case ids. This step is required because `holdout publish` never
   overwrites a different committed SEAL.json; the holdout kit README spells
   it out.
3. The replacement seal commit: the commit that ADDS SEAL.json by name. The
   removal commit is rejected.
4. The first repair commit. The kit computes it from the PATH-MAP
   classification (old map ∪ new map; commits that only touch SEAL.json are
   never repairs). The proof cannot choose it.
5. The active candidate.

The original SEAL.json commit and any seal after the repair are rejected.
Sealed content is never read: the proof is checked from commit topology and
file names only. The holdout kit's own `holdout seal-order` stays its
single-commit integrity check; it is not this proof.

`prerequisites_for` loads the proof. `eligible` and `gate_status` refuse
every B3 and holdout record under a manifest that owes a proof and lacks a
valid one. The case that guided the repair becomes a regression case.
Without the proof, the detection gates are UNMET.

## Manifest series

Manifests are `FREEZE-MANIFEST-<N>.json` in this directory, append-only;
the highest N is active. Each is generated from a gated candidate:

```
python3 docs/design/freeze-v2.12/tools/freeze_manifest.py generate --candidate <C>
python3 docs/design/freeze-v2.12/tools/freeze_manifest.py verify-self --manifest <M>
```

`verify-self` reproduces the git-derived sections and the id from the
candidate. Before a manifest is accepted, a live `freeze_check.py verify`
must pass for every runner profile against the installed runner artifacts.

## Known limitations

- Local hashes cannot prove the remote gateway or model service stayed
  unchanged. The manifest records the gateway configuration and its
  version identifier, and states this limitation.
- The security scan's `--config auto` semgrep rules are fetched live, so
  the rule set is not pinned by the manifest.
- The holdout autopilot never loads the plugin. The measurement launcher is
  bound separately through `holdout_eval_launch.py` and its own runner
  profile.
