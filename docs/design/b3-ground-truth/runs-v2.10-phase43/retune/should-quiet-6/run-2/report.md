I'll run the deep review. Starting with the contract file.

✓ Phase 0 — Resolve scope

No arguments were given, so this is a plain diff review. Assembling the uncommitted diff now.

Mode: diff (uncommitted changes)

Diff is a single 5-line addition to the config model. Moving to the state check.

`.turingmind/` already exists, so the first-run steps are no-ops. Loading triage.

✓ Phase 0.7 — First-run setup (`.turingmind/` already present; nothing to create)

✓ Phase 1 — Triage

Triage is running. Waiting for its result before Phase 1.5 and the deep-only phases.

Coverage discovery found no on-disk artifacts, so the test-sufficiency agent will get an empty block. Waiting on triage before announcing the deep-only phases.

Triage is still running in the background. Nothing else can be announced until its classification arrives, since Phase 1.5, 1c, 1d, and 2c all follow Phase 1 in order. I'll continue the moment it reports back.

Triage returned: Python only, no frameworks, small diff, nothing to skip, CLAUDE.md present (so compliance fires).

⊘ Phase 1.5 — Load intent context (skipped: diff mode, no `$PHASE_ID`)

✓ Phase 1c — Related files

Assembled for the impact agent:

```
<related-files>
  <file path="triggarr/models/config.py">
    <imported-by>triggarr/__main__.py, triggarr/config.py, triggarr/db.py, triggarr/search/engine.py, triggarr/search/scheduler.py, triggarr/startup.py, triggarr/state.py, triggarr/web/middleware.py, triggarr/web/routes.py, tests/conftest.py, tests/test_config.py, tests/test_scheduler.py, tests/test_startup.py, tests/test_web.py (plus 14 other test modules)</imported-by>
    <imports>os, pathlib, typing, urllib.parse, pydantic, pydantic_settings</imports>
    <test-file>tests/test_config.py</test-file>
  </file>
</related-files>
```

✓ Phase 1d — Coverage artifacts

No lcov, cobertura, istanbul, clover, Go, or coverage.py artifacts exist on disk. The test-sufficiency agent gets the empty `<coverage-artifacts></coverage-artifacts>` block.

Config resolved Codex to `auto`, so Phase 2c runs. Loading its file.

✓ Phase 2c — Codex kickoff

Mode is `default` (no args). Gathering the gate facts.

The gate says run, scope working-tree.

▶ Running Codex adversarial review in parallel (GPT-5-codex, ~1–3 min, deep-review only)…

✓ Phase 2 — Dispatching 7 agents in parallel: [bugs (opus), security, architecture (opus), impact, test-sufficiency, compliance, language-python]
✓ Phase 2.5 — Architecture prompt enhancement

Three of seven reviewers and the Codex pass have returned. Waiting on security, impact, compliance, and language-python before Phase 3 can start.

Four of seven back. Still waiting on security, compliance, and language-python.

Five of seven back. Waiting on security and compliance.

Six of seven back. Only compliance remains.

All seven agents and Codex are done. Loading Phase 3 and the Codex collect file.

✓ Phase 3 — Collect, verify, merge, score

Collecting the Codex pass first, then translating it.

Codex joined with one finding. Building the scoring envelope with all six findings and running the scorer.

✓ Phase 4 — Render results

Render gate passed: the pass carries `scored_by_script: true` and the one survivor has band, score, and hash. Dispatch check: all seven native agents plus Codex returned parseable JSON, no foreign attributions.

## Deep Review

**Summary:** Reviewed 1 file, 5 lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| 6 | 1 | 5 |

### Bottom line

The code change itself is correct and safe: it adds a validated setting with a sensible default, and existing installs keep working untouched. The one Critical finding is about what the change does *not* yet do: the new setting is accepted but nothing reads it, so an operator who sets a longer drain timeout in the config or settings UI gets no change in behavior. Every reviewer noted this looks like the deliberate first step of the phase 75 TDD sequence (failing test, then field, then wiring), so this is a "finish the phase before shipping" verdict rather than a "revert" one. Verdict: do not ship this as a release on its own. Wire the scheduler to read the config value, add the settings-save passthrough, and decide on an upper bound. Then re-run.

---

### Critical 🔴
Must fix before commit:

| Agent(s) | File:Line | Issue | Conf | Status |
|----------|-----------|-------|------|--------|
| bugs, architecture, impact, codex-adversarial | `triggarr/models/config.py:139` | Connect the new timeout setting to the shutdown drain | 99 | NEW |

**`triggarr/models/config.py:139` — Connect the new timeout setting to the shutdown drain** (flagged by: codex-adversarial — Connect the new timeout setting to the shutdown drain; bugs — shutdown_drain_timeout config field is never read; the drain still uses only the env var captured at import; architecture — Upper bound for shutdown_drain_timeout lives only in the UI form clamp, not in the pydantic model; bugs — No upper bound: a finite timeout above the container stop grace period passes validation; impact — New field fails closed: an out-of-range or non-finite value aborts config load at startup)

Confidence: 99

*In plain terms:* An operator who sets a longer shutdown drain in the config file or settings page will still get the old 60-second cutoff, so a long search cycle can be cut off mid-shutdown exactly as before.

A supported value such as shutdown_drain_timeout=120.5 is accepted but never consumed. triggarr/search/scheduler.py:70–81 still derives the timeout solely from the environment or a hardcoded 60 seconds, and line 634 uses that constant. With no environment override, shutdown therefore forces resource closure after 60 seconds despite the configured longer drain, potentially interrupting an in-flight search cycle.

The co-located lanes add three related points that were folded into this row:
- **bugs** confirms no reader exists anywhere in `triggarr/` and that the new comment describes behavior ("env overrides at shutdown", "form clamp 3600.0") that is not in the tree yet.
- **bugs and architecture** note there is no `le=` upper bound, unlike the sibling `max_consecutive_failures`. A hand-edited TOML value like `1e9` passes validation, and anything at or above Docker's 90-second stop grace period gets SIGKILLed mid-drain.
- **impact** notes the field fails closed by design: 0, negatives, inf, and nan now abort startup. That is the control working as intended, not a regression.

```
shutdown_drain_timeout: float = Field(default=60.0, ge=1.0, allow_inf_nan=False)
```

Fix direction: Read general.shutdown_drain_timeout when establishing the shutdown timeout, apply the environment override on top, and add an integration test proving a nondefault configuration value reaches the drain.

Why: A configured drain timeout that is silently ignored defeats the purpose of exposing it, and the inline comment currently promises precedence and a ceiling that do not exist.

*The actual patch is produced by the `fix` agent when you accept this finding in the fix loop — it reads the file and edits it semantically, so no diff is pre-baked here.*

---

### Filtered Issues 🔇

*5 issues were not reported:*

| Reason | Count |
|--------|-------|
| Pre-existing (not in diff) | 0 |
| Below confidence threshold | 1 |
| Below min_confidence | 0 |
| Linter territory | 0 |
| Silenced by comment | 0 |
| Absorbed into a co-located finding | 4 |
| Matches intent doc | 0 |

<details>
<summary>View filtered issues</summary>

- `triggarr/models/config.py:139` - shutdown_drain_timeout config field is never read; the drain still uses only the env var captured at import *(absorbed into the Critical row above)*
- `triggarr/models/config.py:139` - Upper bound for shutdown_drain_timeout lives only in the UI form clamp, not in the pydantic model *(absorbed into the Critical row above)*
- `triggarr/models/config.py:139` - No upper bound: a finite timeout above the container stop grace period passes validation *(absorbed into the Critical row above)*
- `triggarr/models/config.py:139` - New field fails closed: an out-of-range or non-finite value aborts config load at startup *(absorbed into the Critical row above)*
- `triggarr/web/routes.py:539` - Saving settings in the UI silently resets a TOML-set shutdown_drain_timeout to 60.0 *(sub-threshold; outside the diff)*

</details>

The routes.py drop is worth a note even though it scored out: the impact agent found that the settings-save handler rebuilds the `general` dict field by field and does not carry `shutdown_drain_timeout` through. Today that is harmless because nothing reads the value. Once the scheduler is wired, any unrelated settings save would silently reset a hand-edited TOML value back to 60. That passthrough belongs in the same plan as the scheduler wiring.

---

### Architectural Notes 📐

- Pattern consistency: ✅ Pydantic `Field` constraints on `GeneralConfig` match the existing `max_consecutive_failures` pattern. `allow_inf_nan=False` is new to the file but is the right tool.
- Documentation: ⚠️ The comment claims "env overrides at shutdown" and "form clamp (3600.0)". Neither is true in HEAD yet. The env value is read once at import, and no 3600 form clamp exists. Re-check after wiring so the comment does not describe behavior that never shipped.
- Dependencies: ✅ No import cycles, new dependencies, cross-module reach-ins, or duplication.
- The field has no consumers yet. Only `triggarr/models/config.py` mentions it. This fits the TDD sequence in the last commit (failing test first).
- Once wired, there will be two sources for one setting. The env reader in scheduler.py uses `max(value, 1.0)` but does not reject inf or nan. An env value of `inf` still unbounds the drain, which breaks the defense-in-depth the new comment claims. The precedence design should validate both sources with the same rules, ideally by reusing the Pydantic constraint.

### Impact Analysis 💥

- Scope: one additive Pydantic field with a default on a model imported by about 28 modules. No constructor signature or call site breaks. Existing TOML configs without the key still validate.
- The field has no consumers yet. Setting it in config.toml today changes nothing at runtime. The design doc at `docs/superpowers/specs/2026-06-02-recovery-counts-config-design.md` says the scheduler should read the config value later with the env var taking precedence.
- Public JSON surface: the debug/config endpoint returns `settings.general.model_dump()`, so it now includes the new key. Not a secret, so no exposure concern.
- The default TOML template in `triggarr/config.py` has commented defaults for sibling fields but no matching line for this one yet, which drifts from the "TOML comments preserved in defaults" convention.
- README and docker-compose "default 60s" text stays accurate. Once a UI clamp allows up to 3600s, docs should warn that values above the 90s stop grace period get SIGKILLed mid-drain.
- No performance, schema, or migration impact. The validator runs once at config load.
- Verdict: shippable as-is from a blast-radius view. The one item to track is the settings-save round-trip, which should land before the scheduler consumes the config value.
- **Files affected:** 1 changed, 28 importers
- **Breaking changes detected:** no

### Test Coverage 🧪

- no coverage data available, skipped

Per-agent attribution: bugs 2 findings, architecture 1, impact 2, codex-adversarial 1, security 0, compliance 0 (ran ruff, clean), language-python 0, test-sufficiency 0.

Paused. Resume with `/vibe-check:deep-review` or close out later with `--finalize`.

**Recap of this deep review**

- **Scope:** one uncommitted change, the new `shutdown_drain_timeout` field on `GeneralConfig`. Seven native reviewers plus a Codex adversarial pass ran. Config was all defaults.
- **Result:** one Critical finding at `triggarr/models/config.py:139`, cross-confirmed by four lanes. The field validates correctly but nothing reads it yet. The scheduler still takes the drain timeout from the env var at import time, so a configured value has no runtime effect. The inline comment also describes an env-override-at-shutdown and a 3600 form clamp that do not exist in the tree.
- **Folded into that row:** no upper bound on the field, unlike its sibling, so a hand-edited huge value would outlast Docker's 90s stop grace period. And the field fails closed on 0, inf, and nan, which is by design.
- **Filtered but worth tracking:** the settings-save handler in routes.py does not carry the new field through, so once the scheduler reads it, any unrelated UI save would reset it to 60. That belongs in the same plan as the wiring.
- **Reviewers who found nothing:** security, compliance (ruff clean), language-python, test-sufficiency (no coverage artifacts on disk).
- **Verdict:** the change is a correct first TDD step for phase 75, not a release candidate on its own. Finish the scheduler wiring, the form passthrough, and the bound decision, then re-run. State is saved so the next pass will mark this finding fixed-since-last automatically.
