# Phase 30: Config surface foundation - Research

**Researched:** 2026-06-30
**Domain:** Config-file ingestion (`tomllib`), Python pure-function/I-O boundary design, orchestrator-prose dispatch wiring for the vibe-check plugin
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 — Python < 3.11 `tomllib` fallback:** When `tomllib` is unavailable (Python < 3.11), **degrade to "no config" + one warning line** — do NOT bundle a minimal fallback TOML parser. The runtime is 3.11+, so the fallback path is effectively dead code; the only hard requirement (spec §2 fail-safe) is that a missing parser never breaks the review.

- **D-02 — What `thresholds` tunes:** The `thresholds` config key tunes the **band boundaries** (critical / warning / medium labels in `band_for()`), NOT the per-command finalize cutoffs (`THRESHOLDS = {"review": 80, "deep-review": 70}`). There are TWO distinct threshold layers in `score.py` — do not conflate them. `band_for(score)` (score.py:86) uses hardcoded boundaries `95` / `80` / `70` — **THIS is what `thresholds` parameterizes.** `THRESHOLDS` (score.py:44) is the per-command finalize cutoff — leave it untouched. **Formula-untouched invariant (spec §5):** the no-config default path MUST stay byte-identical (frozen `GOLDEN_DIGEST` / banding math unchanged when no config present); a `test_score.py` regression case must prove default behavior is byte-stable.

- **D-03 — Where the config is read:** The orchestrator reads `.vibe-check.toml` via a **small, unit-testable Python helper** (e.g. `scripts/config.py` — final name is the planner's call), NOT as Bash/TOML-parsing prose embedded in `commands/review.md`. The helper is the I/O boundary; `score.py` STAYS pure (no filesystem/git I/O — every fact arrives on its stdin envelope). Do NOT make `score.py` read `.vibe-check.toml` itself. The orchestrator calls the helper, gets resolved per-knob values (merged with defaults, warnings collected), passes script-enforced knobs (`thresholds`) into the `score.py` envelope and acts on orchestrator-only knobs (`disabled`, `top_model`) directly. **Precedence (CONFIG-02):** CLI flag > toml value > built-in default, per knob — for Phase 30's three consumers, the toml-vs-default layer must work end-to-end; the flag layer's mechanism is established here.

- **D-04 — Warning verbosity & placement:** Per-key fail-safe warnings surface as **one dedicated "config-health" line near the top of the report** (e.g. `⚠ config: <key> invalid (<reason>) — using default`), NOT inline on each finding. Multiple invalid keys aggregate onto that one config-health block. An absent file produces NO warning (the common zero-config case — CONFIG-01 back-compat).

### Claude's Discretion (planner/executor owns these)

- Exact helper filename/module layout and function signatures.
- Exact envelope key name for `thresholds` and its JSON shape.
- Exact warning-line wording and the config-health block format.
- Which `band_for` literal each `thresholds` sub-key maps to (within D-02's byte-stable constraint).
- README schema-doc layout (CONFIG-04 requires the schema documented; format is open).

### Deferred Ideas (OUT OF SCOPE)

- `min_confidence` / `--min-confidence N` confidence-axis filter — **Phase 31**.
- `idiom_floor` band cap + `// vibe-ignore: <reason>` marker — **Phase 32**.
- Codex `off/auto/on` legibility + safer fix-loop default — **Phase 33**.
- gitleaks (999.2), SARIF (999.3), PR-posting (999.5), measured cost (999.12), docs pass (999.13) — out of v2.8 entirely (spec §5).
- Rewriting the scoring formula / re-deriving `agent_confidence` — explicitly forbidden (spec §5). `thresholds` parameterizes; it does not re-weight.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONFIG-01 | vibe-check reads a repo-root `.vibe-check.toml` once per run; a repo *without* one behaves exactly as v2.7 (zero-config back-compat). | The new config helper resolves the repo-root path once (mirroring review.md step 3's dev-safe resolution); **absent file → all defaults, NO warning, no envelope-key change** so `score.py`'s default-path output is byte-identical (Architecture Patterns §Pattern 2; the GOLDEN_DIGEST + 8 band-boundary tests already lock this). The orchestrator only injects the `thresholds` envelope key when a config value differs from the default — or always injects today's literals as the default, which is byte-equivalent (Pitfall 1). |
| CONFIG-02 | Config resolution follows precedence CLI flag > `.vibe-check.toml` > built-in default, per knob. | Precedence resolved per-knob (Architecture Patterns §Pattern 3). For Phase 30's three consumers only `top_model` has a pre-existing precedence layer today (`$VIBE_CHECK_TOP_MODEL` env var, deep-review.md:55). `thresholds`/`disabled` have no CLI flag yet — the toml-vs-default layer is what proves end-to-end; the flag slot is reserved (later phases add `--min-confidence`, `--codex`). |
| CONFIG-03 | A missing, unparseable, or partially-invalid config degrades **per-key** to defaults with a warning and never aborts a review (fail-safe). | The helper catches `ImportError` (no tomllib), `tomllib.TOMLDecodeError`/`OSError` (unparseable/unreadable), and validates each key independently — one bad key → that key defaults + a collected warning, others apply (Architecture Patterns §Pattern 2; Code Examples). `test_config.py` proves each branch (Validation Architecture). The helper NEVER raises to the orchestrator — it returns `(values, warnings)`. |
| CONFIG-04 | The config can set band `thresholds`, the `disabled` agent roster, and `top_model` — honored at scoring and dispatch respectively. | `thresholds` → injected as a `score.py` envelope key consumed by `band_for()` (Architecture Patterns §Pattern 1; the single `band_for` call site is score.py:810). `disabled` → orchestrator removes agents from the Phase-2 Selection table before dispatch (review.md:527). `top_model` → orchestrator model resolution alongside `$VIBE_CHECK_TOP_MODEL` (deep-review.md:55). |
</phase_requirements>

## Summary

This phase is **not** a library-selection problem — the entire stack is the Python standard library (`tomllib`, already present on the 3.14.5 runtime) plus the plugin's own established patterns. The genuinely hard work is **boundary design and regression discipline**, both of which the codebase has strong precedents for. `score.py` is a deliberately pure function whose import set is pinned to `{json, hashlib, re, sys}` by an AST test (test_score.py:1207); `tomllib` therefore **cannot** live in `score.py`, which is exactly why D-03 mandates a separate helper. The helper is the one module allowed to touch the filesystem; `score.py` keeps seeing only resolved values on its stdin envelope.

The load-bearing invariant for the WHOLE milestone is the **per-key fail-safe** (CONFIG-03): a missing/malformed/partial config degrades each key independently to its default with a loud-but-non-fatal warning. The companion invariant is **byte-stability** (D-02 / spec §5): the no-config path must produce output identical to v2.7. The codebase already protects this with `GOLDEN_DIGEST` (test_score.py:37) and 8 explicit `band_for` boundary assertions (test_score.py:86–111) — those tests are the regression lock the planner must keep green, and a new "default envelope = today's literals" test makes the parameterization provably inert when no config is present.

The three proving consumers split cleanly across the existing enforcement boundary (spec §2 table): `thresholds` is **script-enforced** (a new envelope key `band_for()` reads instead of its literals); `disabled` and `top_model` are **orchestrator-enforced** (dispatch-table edits and model resolution, no `score.py` change). All `tomllib` API facts in this document are verified against the official Python docs.

**Primary recommendation:** Build a new `scripts/config.py` helper (importable + `__main__`-invokable like `score.py`) that returns `(resolved_values, warnings)`; give it `scripts/test_config.py` unit coverage for every fail-safe branch; wire it into `commands/review.md` via the established `python3 - <<'PY'` compound-Bash heredoc (env-var in, stdout JSON out — the mode-5 idiom at review.md:187); parameterize `band_for()` to read an optional `thresholds` envelope key defaulting to today's literals; and add one config-health warning block near the top of the Phase-4 report.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read & parse `.vibe-check.toml` | Config helper (`scripts/config.py`, NEW) | — | The single allowed I/O boundary (D-03); keeps `score.py` pure. `tomllib` import is illegal in `score.py` (AST test). |
| Per-key fail-safe + warning collection | Config helper | Orchestrator (renders the warnings) | Validation is unit-testable Python (D-03); rendering is prose. |
| Precedence resolution (flag > toml > default) | Config helper or orchestrator | — | The helper can accept flag overrides as args, OR the orchestrator merges post-call (Pattern 3 — planner's call). |
| `thresholds` enforcement (banding) | `score.py` (`band_for`) | Orchestrator (passes the envelope key) | Script-enforced math — the single-writer of `band` stays `score.py` (single-banding-path invariant). |
| `disabled` agents enforcement | Orchestrator (Phase-2 dispatch) | — | Dispatch decision; the script never sees agents that didn't run. |
| `top_model` enforcement | Orchestrator (model resolution) | — | Dispatch/model decision; already has a `$VIBE_CHECK_TOP_MODEL` precedent. |
| Config-health warning render | Orchestrator (Phase-4 report header) | — | Prose output near the top of the report (D-04). |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `tomllib` | stdlib (Python ≥ 3.11) | Parse `.vibe-check.toml` | The canonical, zero-dependency TOML reader added to CPython in 3.11. No third-party package needed. `[VERIFIED: docs.python.org/3/library/tomllib]` |
| `json` | stdlib | Serialize the helper's `(values, warnings)` result to stdout for the orchestrator to consume | Already the plugin's orchestrator↔script wire format (`score.py`). `[VERIFIED: score.py:19]` |
| `unittest` | stdlib | Unit-test the helper (every fail-safe branch) | The plugin's established test harness — `python3 -m unittest`, workdir `plugins/vibe-check/scripts`. `[VERIFIED: .orchestrator.json:4-5]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ast` | stdlib | (test-only) extend the import-set guard to the new helper if desired | Optional — the helper is NOT subject to score.py's import ban, but a looser guard (e.g. "no `os.system`/`subprocess`") could pin its I/O surface. Planner's discretion. `[ASSUMED]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `tomllib` | `tomli` (PyPI backport) | Would make the < 3.11 path live, but **D-01 explicitly rejects bundling a parser**. The runtime is 3.14.5 — a backport is pure maintenance burden for dead code. Do NOT add it. |
| A separate `config.py` helper | Inline TOML parsing in `review.md` Bash prose | **D-03 rejects this** — untested markdown prose for the milestone's load-bearing invariant. A Python module gets real `test_*.py` coverage. |
| Helper reads config | `score.py` reads config | **D-03 boundary note + AST test forbid this** — `tomllib` import would fail `test_import_set_subset_of_allowed`. |

**Installation:** None. `tomllib` is in the standard library.

**Version verification:**
```
Runtime: Python 3.14.5 (verified via `python3 --version` in the repo)  [VERIFIED]
tomllib: added in Python 3.11; load(fp, /, *, parse_float=float) requires a BINARY file object;
         raises tomllib.TOMLDecodeError (subclass of ValueError) on invalid TOML.
         [VERIFIED: docs.python.org/3/library/tomllib]
```
The D-01 degrade path (`ImportError` on `import tomllib`) is therefore **effectively dead code** on this runtime but MUST exist per the spec §2 fail-safe.

## Package Legitimacy Audit

> Not applicable — this phase installs **zero** external packages. Every dependency is the Python standard library (`tomllib`, `json`, `unittest`, optionally `ast`), already present on the 3.14.5 runtime. No npm/PyPI/crates install occurs, so slopcheck and registry verification are moot.

## Architecture Patterns

### System Architecture Diagram

```
                            once per run (CONFIG-01)
   .vibe-check.toml  ──────────────────────────────────┐
   (repo root, optional)                                │
                                                        ▼
   CLI flags ───────────────────────►  ┌─────────────────────────────────┐
   (--codex etc. — later phases;        │  scripts/config.py  (NEW helper)│
    none for Phase 30's 3 knobs)        │  - resolve repo-root path       │
                                        │  - import tomllib (ImportError? │
   built-in defaults ──────────────────►│      → degrade, 1 warning, D-01)│
   (today's literals)                   │  - parse (TOMLDecodeError?      │
                                        │      → all defaults + 1 warning)│
                                        │  - per-key validate (bad key?   │
                                        │      → that key default + warn) │
                                        │  - precedence: flag>toml>default│
                                        └────────────┬────────────────────┘
                                                     │ JSON: {values, warnings}
                                                     ▼
                                ┌──────────────  ORCHESTRATOR  ──────────────┐
                                │  (commands/review.md / deep-review.md)      │
                                │                                             │
         script-enforced  ◄─────┤  thresholds ──► into score.py ENVELOPE     │
                                │  disabled   ──► drop rows from Selection    │
         orchestrator-     ◄─────┤                 table BEFORE Phase-2 fan-out│
         enforced               │  top_model  ──► model resolution            │
                                │                 (alongside $VIBE_CHECK_TOP  │
                                │                  _MODEL)                     │
                                │  warnings   ──► config-health block near    │
                                │                 top of Phase-4 report (D-04)│
                                └─────────────────────┬───────────────────────┘
                                                      │ envelope (stdin)
                                                      ▼
                                  ┌────────────────────────────────────┐
                                  │  scripts/score.py  (PURE — unchanged│
                                  │  import set {json,hashlib,re,sys})  │
                                  │  band_for(score, thresholds=None)   │
                                  │   thresholds absent → today's       │
                                  │   95/80/70 literals (byte-stable)   │
                                  └────────────────────────────────────┘
```

Trace the zero-config case (CONFIG-01): no `.vibe-check.toml` → helper returns all defaults + empty warnings → orchestrator injects today's literals (or omits the key) → `band_for` uses 95/80/70 → output byte-identical to v2.7, no warning rendered.

### Recommended Project Structure
```
plugins/vibe-check/
├── scripts/
│   ├── score.py            # UNCHANGED boundary; band_for() gains an optional thresholds param
│   ├── config.py           # NEW — the I/O boundary helper (tomllib lives here)
│   ├── test_score.py       # + thresholds-override + default-byte-stable regression cases
│   └── test_config.py      # NEW — every fail-safe branch (absent/unparseable/bad-key/precedence)
├── commands/
│   ├── review.md           # config read wired in; thresholds → envelope; disabled/top_model dispatch; config-health line
│   └── deep-review.md      # delegates review.md scoring; check top_model/disabled parallel touch
└── (repo root) README.md   # CONFIG-04 schema doc under the existing ## ⚙️ Configuration section
```

### Pattern 1: `thresholds` as an optional, default-inert envelope key (script-enforced)
**What:** `band_for()` reads boundary values from the envelope instead of hardcoded literals, defaulting to today's literals when the key is absent. This is the SAME additive-envelope-key pattern the codebase already uses (`envelope.get(key, default)`, e.g. score.py:682–686).
**When to use:** For the one script-enforced knob in this phase (`thresholds`).
**Example:**
```python
# Source: derived from score.py:86 (band_for) + score.py:682 (envelope.get default pattern)
# band_for currently:
def band_for(score):
    if score >= 95: return "critical"
    if score >= 80: return "warning"
    if score >= 70: return "medium"
    return None

# Parameterized — defaults to today's literals so the no-config path is byte-identical:
_DEFAULT_BANDS = {"critical": 95, "warning": 80, "medium": 70}

def band_for(score, thresholds=None):
    t = thresholds if isinstance(thresholds, dict) else _DEFAULT_BANDS
    crit = t.get("critical", _DEFAULT_BANDS["critical"])
    warn = t.get("warning",  _DEFAULT_BANDS["warning"])
    med  = t.get("medium",   _DEFAULT_BANDS["medium"])
    if score >= crit: return "critical"
    if score >= warn: return "warning"
    if score >= med:  return "medium"
    return None
```
`band_for` is called in exactly ONE place — `run()` at score.py:810 — so `run()` reads `envelope.get("thresholds")` once and threads it to that single call. `[VERIFIED: grep band_for score.py — only score.py:86 def + score.py:810 call]`

> **Open design question for the planner (the genuinely open D-02 mapping) — surfaced, not decided:**
> The design-spec example is `thresholds = { critical = 80, warning = 70 }` (2 keys), but `band_for` has THREE boundaries (95 critical / 80 warning / 70 medium). The mapping is ambiguous and the planner MUST specify it exactly. Two readings, with the coherence trap each carries:
> - **Reading A (sub-keys ARE the boundaries):** `critical=80` means "score ≥ 80 is critical"; `warning=70` means "score ≥ 70 is warning". Under this reading the spec's example REPLACES today's 95→80 (critical floor) and 80→70 (warning floor) and there is no third "medium" boundary in the example — so what is the medium floor? If `medium` defaults to 70 and `warning` is set to 70, the medium band collapses to empty. The planner must decide whether the schema has 2 or 3 sub-keys and what the omitted ones default to.
> - **Reading B (a partial override merged over the 3 defaults):** the example sets `critical`/`warning` and leaves `medium` at its 70 default — but then `critical=80 < warning(default)=80` is incoherent (critical floor not strictly above warning floor).
> **Coherence with the per-command filter (`THRESHOLDS = {"review": 80, "deep-review": 70}`, score.py:44):** the per-command cutoff filters survivors AFTER banding (score.py:824). The `medium` band floor (today 70) must stay ≥ the lowest per-command cutoff (`deep-review`=70) or a banded-medium finding could be produced that the filter then drops — wasteful but not incorrect; lowering `medium` BELOW 70 would band findings that BOTH commands filter out (dead band). The planner should (a) define the exact sub-key set, (b) define defaults for omitted sub-keys, (c) add a validation rule rejecting non-monotonic boundaries (critical > warning > medium) → that key-set defaults + a warning, and (d) keep `medium ≥ 70` coherent with the filter or document why not.
> **Recommended starting point (planner's call):** a 3-sub-key schema `{critical, warning, medium}` each meaning "score ≥ this value earns this band," validated for strict monotonic descent, defaulting the WHOLE set to `{95, 80, 70}` and falling back the WHOLE set (not per-sub-key) to defaults on any monotonicity/type violation — simplest to keep byte-stable and to reason about. `[ASSUMED]`

### Pattern 2: per-key fail-safe helper returning `(values, warnings)` (the milestone keystone)
**What:** The helper NEVER raises to the orchestrator. It returns resolved values + a list of warning strings. Each failure mode degrades independently.
**When to use:** This is CONFIG-03, the load-bearing invariant every later phase assumes.
**Example:**
```python
# Source: synthesized from tomllib official API (verified) + score.py defensive-coercion idiom
#         (e.g. _as_line score.py:842, _category_domain score.py:440 — coerce-or-default, never raise)
def load_config(path, *, flags=None):
    """Return (values, warnings). NEVER raises — the review must not abort (CONFIG-03)."""
    defaults = {"thresholds": None, "disabled": [], "top_model": None}  # None => use built-in
    warnings = []

    try:
        import tomllib
    except ImportError:                                   # D-01: Python < 3.11 — dead code here
        warnings.append("config: tomllib unavailable (Python < 3.11) — using defaults")
        return _apply_flags(defaults, flags), warnings    # absent-parser must not break review

    if not _file_exists(path):                            # ABSENT FILE → defaults, NO warning (CONFIG-01)
        return _apply_flags(defaults, flags), warnings

    try:
        with open(path, "rb") as fh:                      # tomllib.load requires BINARY mode (verified)
            raw = tomllib.load(fh)
    except (tomllib.TOMLDecodeError, OSError) as e:       # unparseable / unreadable → all defaults + 1 warning
        warnings.append("config: .vibe-check.toml unparseable — using defaults")
        return _apply_flags(defaults, flags), warnings

    values = dict(defaults)
    # ----- per-key validation: one bad key defaults THAT key + warns; others apply -----
    values["thresholds"], w = _validate_thresholds(raw)   # returns (value_or_None, warning_or_None)
    if w: warnings.append(w)
    values["disabled"], w = _validate_disabled(raw)
    if w: warnings.append(w)
    values["top_model"], w = _validate_top_model(raw)
    if w: warnings.append(w)

    return _apply_flags(values, flags), warnings           # precedence: flag wins over toml (CONFIG-02)
```
Note: the helper itself does filesystem I/O (`open`), so its `_file_exists` may use `os.path` — that is FINE; **only `score.py` is import-banned**, not `config.py`. (test_score.py:13 explicitly scopes the ban to score.py.)

### Pattern 3: precedence resolution per knob (CONFIG-02)
**What:** flag > toml > default, resolved one knob at a time. Two viable shapes — planner picks:
- **(a) helper takes flags as args** — `load_config(path, flags={...})` applies overrides last (shown above). Centralizes precedence in the unit-tested module. **Recommended.**
- **(b) orchestrator merges post-call** — helper returns toml-vs-default; orchestrator overlays CLI flags in Bash. More wiring in untested prose.
**For Phase 30's three consumers:** only `top_model` has a live precedence today (`$VIBE_CHECK_TOP_MODEL` env, deep-review.md:55). The interaction between that env var and a `top_model` toml key needs a defined order — recommend treating the env var as the existing "flag-tier" value (env > toml > default), so a power user's `$VIBE_CHECK_TOP_MODEL=fable` still wins over a repo's `top_model = "opus"`. `thresholds`/`disabled` have NO flag yet, so the toml-vs-default layer is what proves CONFIG-02 end-to-end. `[ASSUMED — env-vs-toml order is a design choice]`

### Pattern 4: invoke the helper via the established compound-Bash heredoc
**What:** Call `config.py` from `review.md` exactly like the existing mode-5 `python3 - <<'PY' ... PY` heredoc — env vars in, stdout captured to a shell var, no temp file, no `allowed-tools` change.
**Example:**
```bash
# Source: review.md:187 (mode-5 realpath heredoc) + review.md:729 (score.py invocation shape)
# Resolve config helper DEV-SAFE (working-tree FIRST, cache fallback) — mirror review.md step 3's
# $SCORE_PY resolution verbatim, substituting config.py for score.py.
CONFIG_JSON=$(REPO_ROOT="$REPO_ROOT" python3 "$CONFIG_PY")   # config.py reads $REPO_ROOT/.vibe-check.toml, prints {values,warnings}
# parse CONFIG_JSON: extract thresholds (→ envelope), disabled (→ dispatch), top_model (→ model), warnings (→ report)
```
Reuse the SAME dev-safe `$SCORE_PY` resolution block (review.md:697–722, working-tree-first / cache-glob fallback / marketplace fallback / **fail-closed if none**) for `$CONFIG_PY` — BUT note the fail posture differs (see Pitfall 4): a missing **config helper** must degrade to no-config (CONFIG-01), NOT fail closed like a missing scorer. `[VERIFIED: review.md:187, 697-722, 729]`

### Anti-Patterns to Avoid
- **Putting `tomllib` (or any new import) in `score.py`:** fails `test_import_set_subset_of_allowed` (test_score.py:1217). The helper is a SEPARATE module.
- **A second banding path:** `score.py` is the single writer of `band` (CONTEXT.md "single-writer for scored fields"). `thresholds` must flow through the ONE `band_for` call at score.py:810 — do NOT compute bands anywhere else.
- **Warning on an absent file:** CONFIG-01 zero-config back-compat requires SILENCE when no `.vibe-check.toml` exists. Only a present-but-broken file warns.
- **Failing the review on a bad config:** CONFIG-03 — the helper degrades, never aborts. (Contrast with `score.py`'s fail-CLOSED posture, which is correct for a missing SCORER but wrong for a missing CONFIG.)
- **Injecting a non-default `thresholds` envelope key on a zero-config run:** would risk moving the default-path output. Either always inject today's literals (byte-equivalent) OR omit the key when no override — both keep the GOLDEN_DIGEST / band tests green.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML parsing | A regex/line-based TOML reader (the D-01 "minimal fallback parser") | `tomllib` | D-01 explicitly forbids it; tomllib is in stdlib on the 3.14.5 runtime; a hand-rolled parser is a correctness + maintenance burden for a dead path. |
| Config file path resolution | A new path-discovery scheme | The existing review.md step-3 dev-safe resolution idiom (`git rev-parse --show-toplevel` + working-tree-first) | Already audited, fail-safe, and consistent with how `score.py` is resolved. |
| Script↔orchestrator wire format | A bespoke key=value or CLI-arg protocol | A `json.dump` of `{values, warnings}` on stdout, consumed by the orchestrator | Mirrors the `score.py` stdin→stdout JSON envelope the orchestrator already speaks. |
| Defensive coercion of malformed keys | try/except scattered through the orchestrator prose | `isinstance`-guard helpers in `config.py` (the `_as_line` / `_category_domain` coerce-or-default pattern from score.py) | Keeps the never-raise invariant unit-testable; the codebase already proves this pattern works. |

**Key insight:** The whole phase is "lean on the existing pure-function / envelope / dev-safe-resolution / defensive-coercion patterns the plugin already established for `score.py`, and add ONE new module that does the file I/O those patterns deliberately keep out of `score.py`." There is almost nothing novel to invent — the risk is boundary discipline, not algorithm design.

## Runtime State Inventory

> This is a feature-addition phase (a new config surface), NOT a rename/refactor/migration. No stored data, live-service config, OS-registered state, secrets, or build artifacts carry a string that this phase renames.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verified by grep for `.vibe-check.toml`/`tomllib`/`config.py` across `plugins/vibe-check/` (only model-tier env-var references exist; no persisted config state). | None |
| Live service config | None — the `.turingmind/state/` files persist review passes, not config; config is read fresh per run (CONFIG-01). | None |
| OS-registered state | None — no daemons/tasks/units. | None |
| Secrets/env vars | `$VIBE_CHECK_TOP_MODEL` already exists (deep-review.md:55, review.md:553) — NOT renamed; this phase ADDS a `top_model` toml key that composes with it (precedence). `$TURINGMIND_NONINTERACTIVE` exists (unaffected). | None — additive only |
| Build artifacts | None — `scripts/__pycache__/` is stale-tolerant (Python recompiles); no installed-package egg-info. | None |

**Nothing found in any category requiring migration** — this phase only adds a reader and a schema. The one back-compat surface is behavioral, not state: a repo WITHOUT `.vibe-check.toml` must behave byte-identically to v2.7 (CONFIG-01), locked by GOLDEN_DIGEST + the band-boundary tests.

## Common Pitfalls

### Pitfall 1: Moving the GOLDEN_DIGEST / default banding when parameterizing `band_for`
**What goes wrong:** Parameterizing `band_for` accidentally changes the no-config output — a different band on some score, or a re-pinned digest — breaking persisted `medium_acknowledgments` dismissals (keyed on `stable_hash`) and the byte-stability invariant (D-02 / spec §5).
**Why it happens:** Default values diverge from today's literals, or the `thresholds` key gets injected with non-default values on a zero-config run, or `band_for`'s default branch is restructured.
**How to avoid:** Default the WHOLE `thresholds` set to `{critical:95, warning:80, medium:70}`; keep the 8 existing `TestBandBoundaries` assertions (test_score.py:86–111) GREEN unchanged; add a NEW test asserting `band_for(s)` == `band_for(s, None)` == `band_for(s, defaults)` for the boundary values; add a test that a zero-config `run()` envelope (no `thresholds` key) produces the same output as before. The GOLDEN_DIGEST (test_score.py:37) must NOT be re-pinned.
**Warning signs:** Any test in `TestBandBoundaries` or the golden-digest tests turning red; a diff to the `GOLDEN_DIGEST` literal.

### Pitfall 2: tomllib `load()` opened in text mode
**What goes wrong:** `tomllib.load(open(path))` (text mode) raises `TypeError: File must be opened in binary mode`.
**Why it happens:** Training-memory habit from `json.load`, which accepts text files.
**How to avoid:** `open(path, "rb")` — binary mode is REQUIRED. `[VERIFIED: docs.python.org/3/library/tomllib]`
**Warning signs:** A `TypeError` mentioning binary mode in the unparseable-config test.

### Pitfall 3: Catching the wrong exception for unparseable TOML
**What goes wrong:** Catching `json.JSONDecodeError` or a bare `Exception`, missing or over-broadening the real failure.
**Why it happens:** The exception is `tomllib.TOMLDecodeError` (a `ValueError` subclass) — not obvious without checking docs.
**How to avoid:** Catch `tomllib.TOMLDecodeError` for malformed TOML and `OSError` for unreadable files; do NOT swallow everything (the never-raise invariant should be expressed by handling the KNOWN failure modes, not by a blanket `except Exception`). `[VERIFIED: docs.python.org/3/library/tomllib — TOMLDecodeError subclasses ValueError]`
**Warning signs:** An unparseable-config test that passes by accident (blanket except) or a malformed file that still aborts the run.

### Pitfall 4: Reusing score.py's FAIL-CLOSED posture for the config helper
**What goes wrong:** Copying review.md step 3's "fail closed if the script is absent" into the config-helper resolution makes a missing/unresolvable `config.py` ABORT the review — directly violating CONFIG-01/CONFIG-03 (config problems must degrade, never break).
**Why it happens:** The dev-safe RESOLUTION block (working-tree-first/cache-fallback) is shared, and it ends in `exit 1` for `score.py`.
**How to avoid:** Reuse the resolution ORDER but change the terminal posture: if `$CONFIG_PY` resolves to nothing, degrade to no-config (all defaults, optionally one warning), do NOT `exit 1`. The scorer is mandatory (no scoring → no honest report); the config reader is optional (no config → v2.7 behavior).
**Warning signs:** A repo with no installed config helper aborting instead of running with defaults.

### Pitfall 5: `disabled` removing a mandatory agent
**What goes wrong:** A user disables `bugs` or `security` (the two always-on agents, review.md:531–532), silently gutting coverage.
**Why it happens:** `disabled` is applied as a blanket roster subtraction.
**How to avoid:** Decide a policy (planner's call): either honor any disable (user's repo, user's call — but then the config-health line should NOTE that a core agent was disabled, for the audit trail), OR refuse to disable `bugs`/`security` and warn. Recommend honoring with a visible note, consistent with "never silently drop." The design-spec example disables `language-go` (a language agent), so the common case is language/framework agents. `[ASSUMED — policy is a design choice]`
**Warning signs:** A review that dispatches zero of the always-on agents with no visible reason.

### Pitfall 6: `top_model` accepting an unvalidated value
**What goes wrong:** A `top_model = "gpt-5"` config silently passes a bogus model into Task calls.
**Why it happens:** No allowlist check on the toml value.
**How to avoid:** Mirror the EXISTING `$VIBE_CHECK_TOP_MODEL` validation (deep-review.md:55): only `opus`/`fable` are valid; anything else falls back to `opus` with a one-time warning. The toml key should reuse that exact allowlist + fallback so the two precedence sources can't diverge. `[VERIFIED: deep-review.md:55]`
**Warning signs:** An unrecognized model string reaching a Task dispatch.

## Code Examples

### Verified tomllib usage (the parse + binary-mode + exception shape)
```python
# Source: docs.python.org/3/library/tomllib  [VERIFIED]
import tomllib                                   # ImportError on Python < 3.11 (D-01 degrade)
try:
    with open("pyproject.toml", "rb") as f:      # BINARY mode required
        data = tomllib.load(f)                   # load(fp, /, *, parse_float=float)
except tomllib.TOMLDecodeError:                  # subclass of ValueError
    ...                                          # malformed TOML
# tomllib.loads(s, /, *, parse_float=float) also available for a string
```

### The existing envelope-key default idiom score.py already uses (the template to copy)
```python
# Source: score.py:682-686  [VERIFIED]
command = envelope.get("command", "review")
all_mode = bool(envelope.get("all_mode", False))
changed_line_ranges = envelope.get("changed_line_ranges", {}) or {}
# → thresholds follows the SAME shape:
thresholds = envelope.get("thresholds")          # None when absent → band_for uses today's literals
```

### The existing compound-Bash heredoc to mirror for the helper invocation
```bash
# Source: review.md:187  [VERIFIED]
REAL=$(ROOT="$ROOT" LP="$LITERAL_PREFIX" python3 - <<'PY' 2>/dev/null
import os, sys
...
PY
)
# The config-helper call follows the same env-var-in / stdout-out / capture-to-var shape,
# but invokes the resolved $CONFIG_PY file (like review.md:729's `python3 "$SCORE_PY"`) rather
# than an inline heredoc, so the helper stays a real, importable, unit-tested module.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Third-party `toml` / `tomli` packages for reading TOML | `tomllib` in the standard library | Python 3.11 (Oct 2022) | Zero-dependency TOML reading; no install. This is why the stack table needs no PyPI package. `[VERIFIED: docs.python.org/3/library/tomllib]` |
| Config as untested Bash prose | Config as a unit-tested Python helper module | This phase (D-03) | The milestone's load-bearing invariant gets real test coverage instead of markdown. |

**Deprecated/outdated:**
- `tomli` backport: irrelevant on a 3.11+ runtime and explicitly rejected by D-01. Do not add.
- Fixed thinking budgets in Task calls: deprecated API-wide (deep-review.md:82) — not relevant to this phase but worth not re-introducing while editing model-resolution prose.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A 3-sub-key `{critical,warning,medium}` thresholds schema with strict-monotonic validation and whole-set default fallback is the cleanest mapping | Pattern 1 (D-02 open question) | If the owner intended the 2-key spec example literally, the schema shape differs — but the planner explicitly owns this (CONTEXT.md Claude's Discretion), so the RISK is "planner re-decides," not "wrong code ships." LOW. |
| A2 | `$VIBE_CHECK_TOP_MODEL` env should be treated as the flag-tier (env > toml > default) so a power-user override still wins | Pattern 3 / Pitfall 6 | If the desired order is toml > env, a repo config would override a user's shell env. Needs a one-line confirmation at plan/discuss time. MEDIUM. |
| A3 | `disabled` should honor disabling any agent (incl. bugs/security) WITH a visible config-health note, rather than refusing | Pitfall 5 | If the owner wants core agents un-disable-able, the policy flips. It's the user's own repo, so honoring-with-note is defensible, but it's a coverage-safety call worth confirming. MEDIUM. |
| A4 | An optional looser import-guard on `config.py` (no `subprocess`/`os.system`) is nice-to-have, not required | Supporting stack | None — purely additive test hardening; omitting it changes nothing functional. LOW. |
| A5 | The config helper resolves its file path via the SAME dev-safe block as score.py but with a degrade (not fail-closed) terminal posture | Pattern 4 / Pitfall 4 | If a different resolution is wanted, wiring differs — but degrade-not-abort is mandated by CONFIG-01/03, so the posture itself is locked; only the resolution ORDER is the assumption. LOW. |

## Open Questions (RESOLVED)

> All three were the planner's calls to make; each is now LOCKED inside the
> Phase-30 plans. Markers added 2026-06-30 after the plan-checker pass.

1. **The exact `thresholds` sub-key→boundary mapping and validation (D-02).**
   - What we know: `band_for` has 3 boundaries (95/80/70, single call site at score.py:810); the spec example shows 2 sub-keys (`critical=80, warning=70`); the per-command filter (`THRESHOLDS`, score.py:44) runs after banding and must stay coherent with the `medium` floor.
   - What's unclear: 2-key vs 3-key schema; defaults for omitted sub-keys; monotonicity rule; whether `medium` may drop below the deep-review cutoff (70).
   - Recommendation: planner specifies a 3-sub-key schema with strict-monotonic validation and whole-set default fallback (Pattern 1); pin it with a thresholds-override test AND a default-byte-stable test. This is explicitly the planner's call (CONTEXT.md Discretion) — research's job is to surface the coherence trap, which it does.
   - **RESOLVED:** LOCKED in `30-01-PLAN.md` (3-sub-key `{critical, warning, medium}`, each an int in `[1,100]`, strictly descending, `medium ≥ 70`, whole-set fallback to the built-in 95/80/70 + one warning) and consumed verbatim in `30-02-PLAN.md`'s interface block. Default path stays byte-identical (GOLDEN_DIGEST + 8 TestBandBoundaries unchanged).

2. **`top_model` env-vs-toml precedence (A2) and `disabled` core-agent policy (A3).**
   - What we know: `$VIBE_CHECK_TOP_MODEL` already exists with opus/fable validation; `bugs`+`security` are always-on.
   - What's unclear: the merge order with the new toml keys; whether core agents are un-disable-able.
   - Recommendation: env > toml > default for the model; honor `disabled` with a visible config-health note. Both are cheap to confirm at plan/discuss time and are flagged in the Assumptions Log.
   - **RESOLVED:** LOCKED in `30-03-PLAN.md` — `$VIBE_CHECK_TOP_MODEL` (env) > `top_model` (toml) > `opus` (default), reusing the opus/fable allowlist for both sources; `disabled` is honored (user's repo) but a disabled core agent (`bugs`/`security`) is announced on the config-health line.

3. **Does `deep-review.md` need a parallel config touch, or only `review.md`?**
   - What we know: deep-review.md delegates review.md's scoring Phase verbatim (so `thresholds` flows through for free), but it OWNS its own top-model resolution (deep-review.md:55) and its own agent-selection table (the "Differences" section).
   - What's unclear: whether `top_model` (toml) and `disabled` need to be applied in deep-review.md's dispatch/model-resolution prose in addition to review.md.
   - Recommendation: plan for `thresholds` to be review.md-only (inherited by deep), but `top_model`/`disabled` to touch BOTH command files where each resolves its own dispatch/model — verify during planning by reading deep-review.md's model-resolution and Selection-table prose. Likely a small parallel edit, consistent with how the milestone treats these as shared wiring files (SEQUENTIAL discipline, STATE.md).
   - **RESOLVED:** stated verbatim in `30-03-PLAN.md` — `thresholds` is review.md-only (inherited by deep-review via delegation); `top_model` + `disabled` touch BOTH command files where each resolves its own dispatch/model.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | The config helper + score.py + tests | ✓ | 3.14.5 | — |
| `tomllib` | Parsing `.vibe-check.toml` (CONFIG-01) | ✓ | stdlib (≥3.11) | D-01 degrade-to-no-config (dead path on this runtime) |
| `unittest` | `test_config.py` / `test_score.py` | ✓ | stdlib | — |
| git | Repo-root resolution (`git rev-parse --show-toplevel`) | ✓ (repo is a git repo) | — | empty `$REPO_ROOT` → degrade per Pitfall 4 |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** `tomllib` on a hypothetical < 3.11 runtime — D-01 degrade path. Effectively dead code on 3.14.5 but must exist (spec §2 fail-safe).

## Validation Architecture

> `.planning/config.json` was not found at research time; per the rule (absent key = enabled), the Validation Architecture section IS included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib) |
| Config file | none — discovery via `python3 -m unittest`; harness pinned by `.orchestrator.json` |
| Quick run command | `cd plugins/vibe-check/scripts && python3 -m unittest` |
| Full suite command | `cd plugins/vibe-check/scripts && python3 -m unittest` (single suite; 147 tests today, all green — verified) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONFIG-01 | Absent `.vibe-check.toml` → all defaults, NO warning | unit | `python3 -m unittest test_config.TestFailSafe.test_absent_file_silent_defaults` | ❌ Wave 0 (`test_config.py` new) |
| CONFIG-01 | Zero-config `run()` envelope (no thresholds key) byte-identical to v2.7 | unit | `python3 -m unittest test_score.TestBandBoundaries` (KEEP green) + a new `test_default_envelope_byte_stable` | ⚠ partial (band tests exist test_score.py:86; default-envelope test new) |
| CONFIG-02 | flag > toml > default per knob (toml-vs-default proven for the 3 knobs; flag slot for top_model) | unit | `python3 -m unittest test_config.TestPrecedence` | ❌ Wave 0 |
| CONFIG-03 | Unparseable TOML → defaults + 1 warning, no raise | unit | `python3 -m unittest test_config.TestFailSafe.test_unparseable_defaults_plus_warning` | ❌ Wave 0 |
| CONFIG-03 | One invalid key (bad type / out-of-range / unknown band) → that key defaults + warning, others apply | unit | `python3 -m unittest test_config.TestFailSafe.test_one_bad_key_isolated` | ❌ Wave 0 |
| CONFIG-03 | `ImportError` (no tomllib) → defaults + 1 warning, no raise (D-01) | unit | `python3 -m unittest test_config.TestFailSafe.test_no_tomllib_degrades` (monkeypatch import) | ❌ Wave 0 |
| CONFIG-04 | `thresholds` override changes banding | unit | `python3 -m unittest test_score.TestThresholdsOverride` | ❌ Wave 0 (in `test_score.py`) |
| CONFIG-04 | `disabled` / `top_model` honored at dispatch/model | smoke (orchestrator-only) | Phase 34 planted-fixture smoke proof (per spec §4 — orchestrator knobs are NOT unit-tested) | n/a (Phase 34) |

### Sampling Rate
- **Per task commit:** `cd plugins/vibe-check/scripts && python3 -m unittest`
- **Per wave merge:** same (single fast suite, ~0.12s for 147 tests)
- **Phase gate:** Full suite green + a clean deep-review before any merge (SEQUENTIAL discipline, STATE.md; CLOSE-01 requires every phase clean before the Phase-34 bump).

### Wave 0 Gaps
- [ ] `plugins/vibe-check/scripts/test_config.py` — NEW; covers CONFIG-01/02/03 fail-safe + precedence branches.
- [ ] `plugins/vibe-check/scripts/test_score.py` — ADD a `TestThresholdsOverride` class (override changes banding) AND a default-byte-stable regression case (no-config envelope == today's output; GOLDEN_DIGEST unchanged).
- [ ] Framework install: none — `unittest` is stdlib; harness already exists.

*The `disabled`/`top_model` orchestrator knobs are proven by the Phase-34 planted-fixture smoke test per spec §4, NOT by unit tests — do not author orchestrator-dispatch unit tests this phase.*

## Security Domain

> `security_enforcement` config not found at research time (absent = enabled), so this section IS included. This phase's attack surface is narrow (reading a repo-local config file) but real.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface — local CLI tool reading a local file. |
| V3 Session Management | no | No sessions. |
| V4 Access Control | no | No multi-user access control. |
| V5 Input Validation | **yes** | `.vibe-check.toml` is **untrusted input** (it lives in the repo under review). Validate every key: type-check, allowlist (`top_model` ∈ {opus,fable}), range/monotonicity (`thresholds`), and treat all values as inert DATA — never as code, paths to exec, or model strings passed unvalidated to dispatch. `tomllib` itself does not execute TOML (no code-exec vector like YAML's), but the VALUES must still be validated before they steer banding/dispatch. |
| V6 Cryptography | no | No new crypto. `stable_hash` (sha256) is unchanged and must STAY unchanged (GOLDEN_DIGEST). |

### Known Threat Patterns for {Python config ingestion + LLM-orchestrator dispatch}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/oversized config aborting the review (DoS) | Denial of Service | Never-raise helper (CONFIG-03) — degrade to defaults; the review always runs. |
| `top_model` injecting an arbitrary/bogus model into Task dispatch | Tampering | Allowlist {opus,fable} + fallback-to-opus + warning, reusing the existing `$VIBE_CHECK_TOP_MODEL` validation (deep-review.md:55) so the two sources can't diverge. |
| `disabled` silently gutting coverage (disable bugs/security) | Tampering / Repudiation | Honor-with-visible-note (or refuse) per policy (Pitfall 5) — the config-health line keeps an audit trail; "never silently drop." |
| A config value treated as a path/command and shelled out | Tampering / Elevation | Config values are DATA only — none flow into `subprocess`/`exec`/a path that is opened-and-run. The helper opens ONLY the fixed `.vibe-check.toml` path (repo-root-resolved), never a config-supplied path. Aligns with the global CLAUDE.md absolute rule (no user input → subprocess/exec without allowlist). |
| Config-supplied warning text injected into the report verbatim | Tampering (output) | Warnings name the KEY and a fixed reason string — do NOT echo raw attacker-controlled value text into the report unescaped (mirror score.py's "treat agent_notes as inert display text" posture, deep-review.md:360). |
| `thresholds` set to band everything critical (noise/Repudiation) | Tampering | Monotonicity + range validation; out-of-range → whole-set default + warning. It's the user's own repo, so the worst case is self-inflicted noise, surfaced by the config-health line. |

## Sources

### Primary (HIGH confidence)
- `docs.python.org/3/library/tomllib` — verified: `load(fp,/,*,parse_float=float)` requires a binary file object; `loads(s,/,*,parse_float=float)`; `TOMLDecodeError` subclasses `ValueError`; added in Python 3.11.
- `plugins/vibe-check/scripts/score.py` — `band_for` (line 86, single call site line 810); `THRESHOLDS` (line 44); `run()` envelope.get defaults (lines 682–686); import set {json,hashlib,re,sys} (line 11); defensive coercion idioms (`_as_line` 842, `_category_domain` 440).
- `plugins/vibe-check/scripts/test_score.py` — `GOLDEN_DIGEST` (line 37); `TestBandBoundaries` (lines 86–111); AST import-set test (lines 1207–1262); ban scoped to score.py only (line 13).
- `plugins/vibe-check/commands/review.md` — score.py dev-safe resolution + fail-closed (lines 697–722); envelope build/invocation (lines 724–741); compound-Bash python3 heredoc idiom (line 187); Phase-2 Selection table (lines 527–545); Phase-4 report header (`## Code Review`, line 782).
- `plugins/vibe-check/commands/deep-review.md` — top-model resolution + opus/fable validation (line 55); delegates review.md scoring; agent-selection "Differences" table.
- `.orchestrator.json` — `test_verify_cmd: python3 -m unittest`, workdir `plugins/vibe-check/scripts`.
- `README.md` — existing `## ⚙️ Configuration` section + `VIBE_CHECK_TOP_MODEL` table (lines 59–74) — the doc convention CONFIG-04 extends.
- `docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md` — §1 schema, §2 who-reads/enforces table + precedence + fail-safe, §3 Phase 30, §4 testing/DoD, §5 out-of-scope.
- Local runtime: `python3 --version` → 3.14.5; `python3 -m unittest` → 147 tests OK (verified this session).

### Secondary (MEDIUM confidence)
- None required — every claim is anchored to a primary source above.

### Tertiary (LOW confidence)
- The `thresholds` sub-key mapping recommendation (Pattern 1) and the env-vs-toml / disabled-policy choices (Assumptions A2/A3) are reasoned design recommendations, explicitly flagged for planner confirmation — NOT asserted facts.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — entirely stdlib; `tomllib` API verified against official docs; runtime version verified locally.
- Architecture: HIGH — all patterns are direct lifts of existing, test-locked codebase idioms (pure-function boundary, envelope-key defaults, dev-safe resolution, defensive coercion); the AST import-ban concretely forces the D-03 separate-helper design.
- Pitfalls: HIGH — each pitfall is grounded in a specific code line or a verified API fact (binary-mode, exception class, fail-closed-vs-degrade, single band writer).
- Open design questions (thresholds mapping, precedence order, disabled policy): MEDIUM — these are genuine design choices the planner/owner must lock; research surfaces the traps and recommends, but does not (and per CONTEXT.md Discretion, must not) decide them.

**Research date:** 2026-06-30
**Valid until:** 2026-07-30 (stable — stdlib + internal patterns; nothing fast-moving)
