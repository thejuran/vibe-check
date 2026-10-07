Starting the deep review. Reading the contract first, then the bootstrap.

All four helper paths bound. Now Phase 0.

✓ Phase 0 — Resolve scope

No arguments were passed, so this is the default diff mode. Assembling the diff.

Mode: diff (uncommitted changes)

The diff is one five-line change in the config model. HEAD is detached (branch shows empty). Now Phase 0.5.

✓ Phase 0.5 — Multi-pass state check

No state file for this detached-HEAD key, so this is pass 1. Reading the config and first-run phase files.

✓ Phase 0.6 — Resolve config

✓ Phase 1 — Triage

Taking the git-safety snapshot first, in its own turn.

Snapshot taken. Dispatching the triage agent.

Triage is running in the background. I'll wait for its result before moving on, since Phase 1.5 and the deep-only phases depend on it.

Triage: Python only, no frameworks, small diff, intent docs found is CLAUDE.md only.

⊘ Phase 1.5 — Load intent context (skipped: not GSD phase mode)

✓ Phase 1c — Related files

Related files assembled. Next I need the coverage-artifacts phase file and the Codex kickoff file, so reading both now.

✓ Phase 1d — Coverage artifacts

No coverage artifacts exist on disk, so the injected block is the empty one. Running the coverage gate and the Codex facts gathering now.

Codex is launched. Now the Phase 2 pre-dispatch reads: dispatch, deep selection, and the architecture prompt file.

Codex finished and the bugs agent has returned. Five agents are still running. I'll wait for all of them before entering Phase 3.

Architecture is back with notes and no findings. Four agents still running: security, impact, compliance, language-python.

Security returned clean. Waiting on impact, compliance, and language-python.

Impact is back. Still waiting on compliance and language-python.

Python agent returned clean. Only compliance remains.

All six agents have returned. Reading the Phase 3 files, including the Codex join.

✓ Phase 3 — Collect, verify, merge, score

Collecting the Codex pass first, then the git-safety gate.

Codex joined with one finding. Now the git-safety gate and the source windows for the scorer.

✓ Codex joined — 1 findings (1 cross-confirmed)

Scoring produced one Critical finding, confirmed by three lanes. Reading the render phase.

## Deep Review

**Summary:** Reviewed 1 file, 5 lines changed

| Found | Reported | Filtered |
|-------|----------|----------|
| 5 | 1 | 4 |

### Bottom line

This change is an intermediate test-first step. It adds a configurable shutdown drain timeout to the settings model, with sane bounds, and the field itself is correct and matches the existing conventions. But nothing reads it yet. If you shipped this as-is, an operator who sets the value in their config file would see it accepted and silently ignored, and the shutdown drain would keep using the old environment variable or the 60-second default. Verdict: fine to commit as the first slice of phase 75, but do not release until the scheduler, the settings save path, and the UI clamp are wired up in the follow-on plans.

---

### Critical 🔴
Must fix before commit:

| Agent(s) | File:Line | Issue | Conf | Status |
|----------|-----------|-------|------|--------|
| codex-adversarial, bugs, impact | `triggarr/models/config.py:139` | Wire the new timeout setting into the shutdown drain | 99 | NEW |

**`triggarr/models/config.py:139` — Wire the new timeout setting into the shutdown drain** (flagged by: codex-adversarial — Wire the new timeout setting into the shutdown drain; bugs — shutdown_drain_timeout config field is not read anywhere, so setting it has no effect; impact — New shutdown_drain_timeout field is not yet read by anything (scheduler still uses only the env var); bugs — No upper bound on the model; the 3600s ceiling is enforced only by the form clamp)

Confidence: 99

*In plain terms:* An operator who sets a longer drain timeout in the config file will still have in-flight searches cut off after 60 seconds at shutdown, because the new setting does not reach the code that performs the drain.

GeneralConfig(shutdown_drain_timeout=120.5) accepts and preserves the value, but shutdown still uses _SHUTDOWN_DRAIN_TIMEOUT, initialized solely from the environment or 60.0 in triggarr/search/scheduler.py:58–81 and passed to asyncio.timeout at line 634. Thus an operator configuring a longer drain still gets forced resource closure after 60 seconds. No runtime consumer reads the new field.

The two absorbed bugs-lane members add: the field has no upper bound, so a hand-edited TOML value such as 1e9 passes validation and would hold shutdown past the container's stop grace period, whereas the sibling field `max_consecutive_failures` sets both floor and ceiling. The impact lane also notes the settings save path in routes.py builds the general dict from a fixed key list and would drop a TOML-set value on the next UI save.

```
shutdown_drain_timeout: float = Field(default=60.0, ge=1.0, allow_inf_nan=False)
```

Fix direction: Use the active general.shutdown_drain_timeout as the shutdown default, preserving the environment override, and add an integration test proving a non-default configuration reaches the drain timeout.

Why: GeneralConfig(shutdown_drain_timeout=120.5) accepts and preserves the value, but shutdown still uses _SHUTDOWN_DRAIN_TIMEOUT, initialized solely from the environment or 60.0 in triggarr/search/scheduler.py:58–81 and passed to asyncio.timeout at line 634. Thus an operator configuring a longer drain still gets forced resource closure after 60 seconds. No runtime consumer reads the new field.

*The actual patch is produced by the `fix` agent when you accept this finding in the fix loop — it reads the file and edits it semantically, so no diff is pre-baked here.*

---

### Filtered Issues 🔇

*4 issues were not reported:*

| Reason | Count |
|--------|-------|
| Pre-existing (not in diff) | 0 |
| Below confidence threshold | 1 |
| Below min_confidence | 0 |
| Linter territory | 0 |
| Silenced by comment | 0 |
| Absorbed into a co-located finding | 3 |
| Matches intent doc | 0 |

<details>
<summary>View filtered issues</summary>

- `triggarr/models/config.py:139` - shutdown_drain_timeout config field is not read anywhere, so setting it has no effect *(absorbed into the Critical finding above)*
- `triggarr/models/config.py:139` - New shutdown_drain_timeout field is not yet read by anything (scheduler still uses only the env var) *(absorbed into the Critical finding above)*
- `triggarr/models/config.py:139` - No upper bound on the model; the 3600s ceiling is enforced only by the form clamp *(absorbed into the Critical finding above)*
- `triggarr/web/routes.py:540` - Saving settings from the UI silently resets a TOML-configured shutdown_drain_timeout to 60.0 *(sub-threshold)*

</details>

---

### Architectural Notes 📐

- Pattern consistency: ✅ The field follows the bounded-Field pattern already used in the same class, and the tag-comment convention (DEBT-06 beside SAFETY-03 and v2.2).
- Documentation: ⚠️ The new comment describes behavior not yet built: config as default, env override at shutdown, and a 3600.0 form clamp. No such clamp exists in routes.py yet, and the scheduler reads the env var at import time rather than at shutdown.
- Dependencies: ✅ No new imports, cycles, cross-module reach-ins or duplication. The module still imports only pydantic and pydantic_settings.
- Design risk when wired: the drain timeout will have two sources with different validation. The Pydantic field rejects inf and nan, but the existing env reader uses `max(float(raw), 1.0)`, which lets inf through and returns nan for nan. Both sources should go through one finite-only helper.
- Lifecycle: the scheduler freezes the env value into a module constant at import. When the field is wired, the timeout must be resolved at shutdown from live config plus env, or a UI edit will not take effect until restart.

### Impact Analysis 💥

- Change class: one new optional field with a default and tightened validation. Existing config files have no such key and load unchanged with the 60.0 default. No previously accepted input is now rejected.
- Public API: GeneralConfig gains a field, none removed or renamed. The nine importers are unaffected. The config export endpoint will now include the new key, which adds output but breaks nothing.
- Validation scope: a TOML value below 1.0, inf or nan now fails to load at startup. No deployment could have such a value because the field did not exist before.
- Env path gap, pre-existing and out of scope: the scheduler's env reader may accept an inf value. The new guard covers only the TOML path.
- Schema, DB, perf: none.
- Blast radius: minimal right now because nothing consumes the field. The main follow-up risk is the settings save path dropping the field on every UI save until the form wiring lands.
- Verdict: shippable as an intermediate commit. Before the phase is called complete, wire the field into the settings save path and into the scheduler's drain read.
- **Files affected:** 1 changed, 9 importers, 3 related test files
- **Breaking changes detected:** no

### Test Coverage 🧪

- no coverage data available, skipped (no coverage artifact found)

Proceeding to persist state.

✓ Phase 4.5 — Persist pass state

State persisted. Phase 5 applies: findings exist, default diff mode, not finalize. Reading the fix-loop phase.

✓ Phase 5 — Interactive fix loop

Paused. Resume with `/vibe-check:deep-review` or close out later with `--finalize`.

**Recap of this pass.** The diff adds one bounded `shutdown_drain_timeout` field to the settings model. Seven lanes reviewed it: six native agents plus Codex. The field itself is clean on security, Python idiom, compliance, and pattern consistency. The one Critical finding, confirmed by Codex, bugs, and impact, is that nothing reads the new field yet: the scheduler still takes the drain timeout from the environment variable at import time, so a config value is accepted and ignored. Two secondary points were folded into it: the model has no upper bound while the sibling field does, and the settings save path in routes.py would drop a config-file value on the next UI save. All of this is expected for a test-first first slice of phase 75, and plans 75-02 through 75-04 are where the wiring belongs.

**Nothing was changed.** State is saved for pass 1 under `.turingmind/state/`, so the next run will carry this finding forward and mark it fixed once the scheduler wiring lands.
