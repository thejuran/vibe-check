# Phase 30: Config surface foundation - Context

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the repo-level `.vibe-check.toml` config surface — the keystone of the v2.8
milestone. The orchestrator resolves the repo-root path once per run (`tomllib`
with graceful degradation), applies the precedence chain (CLI flag > toml >
built-in default) per knob, and degrades a missing/malformed/partial config
**per-key** to defaults with a warning, **never fatally**. Three simplest
consumers prove the surface end-to-end: `thresholds` (a `score.py` envelope key),
plus `disabled` agents + `top_model` (orchestrator dispatch decisions).

Requirements: CONFIG-01, CONFIG-02, CONFIG-03, CONFIG-04.

The remaining knobs (`min_confidence`, `idiom_floor`, `vibe-ignore`, Codex
legibility, fix-loop default) are LATER phases (31-33) and are out of scope here —
this phase only builds the surface and wires the three proving consumers.
</domain>

<decisions>
## Implementation Decisions

These four were surfaced as the open implementation gray areas (the design spec
locks everything else). The owner declined to adjudicate the technical details and
confirmed "use your recommendations" — so each is locked to the recommended
default below, framed for the planner.

### Python < 3.11 `tomllib` fallback
- **D-01:** When `tomllib` is unavailable (Python < 3.11), **degrade to "no
  config" + one warning line** — do NOT bundle a minimal fallback TOML parser.
  Rationale: the runtime is 3.11+, so the fallback path is effectively dead code;
  a hand-rolled parser is maintenance + correctness burden for a path that won't
  execute. The only hard requirement (from the spec §2 fail-safe) is that a missing
  parser never breaks the review — degrade-to-defaults satisfies it. This resolves
  the open plan-time call flagged in STATE.md.

### What `thresholds` tunes
- **D-02:** The `thresholds` config key tunes the **band boundaries**
  (critical / warning / medium labels in `band_for()`), NOT the per-command
  finalize cutoffs (`THRESHOLDS = {"review": 80, "deep-review": 70}`). This matches
  the design-spec illustrative schema `thresholds = { critical = 80, warning = 70 }`
  and is the intuitive "what counts as critical/warning" knob.
  - **Technical note for the planner — there are TWO distinct threshold layers in
    `score.py`, do not conflate them:**
    - `band_for(score)` (score.py:86) uses hardcoded boundaries `95` (critical) /
      `80` (warning) / `70` (medium). **THIS is what `thresholds` parameterizes.**
      The config example `{critical=80, warning=70}` maps to `band_for`'s warning
      and (implicitly) lower boundaries — the planner must define exactly which
      literals each config key replaces and keep `medium`'s `70` floor coherent
      with the per-command filter below.
    - `THRESHOLDS = {"review": 80, "deep-review": 70}` (score.py:44) is the
      per-command *finalize cutoff* (which findings surface for `/review` vs
      `/deep-review`). **This is NOT what the `thresholds` config knob tunes** —
      leave it untouched this phase.
  - **Formula-untouched invariant (spec §5):** `thresholds` *parameterizes* the
    existing band cutoffs — it does not re-weight scoring. The no-config default
    path MUST stay byte-identical (the frozen `GOLDEN_DIGEST` / banding math is
    unchanged when no config is present). A `test_score.py` regression case must
    prove default behavior is byte-stable.

### Where the config is read
- **D-03:** The orchestrator reads `.vibe-check.toml` via a **small, unit-testable
  Python helper** (e.g. `scripts/config.py` — final name is the planner's call,
  following the `score.py` sibling convention), NOT as Bash/TOML-parsing prose
  embedded in `commands/review.md`. Rationale: the per-key fail-safe is the
  load-bearing invariant for the WHOLE milestone; a Python helper gets real
  `test_*.py` unit coverage (unparseable file, invalid key type, out-of-range
  value, unknown band name) exactly like `score.py`, instead of untested markdown
  prose. The orchestrator calls the helper, gets back the resolved per-knob values
  (already merged with defaults, warnings collected), then passes script-enforced
  knobs (`thresholds`) into the `score.py` envelope and acts on orchestrator-only
  knobs (`disabled`, `top_model`) directly.
  - **Boundary note:** this respects the existing pure-function `score.py`
    boundary (score.py does NO filesystem/git I/O — every fact arrives on stdin).
    The config helper is the one allowed to read the file from disk; `score.py`
    still only ever sees resolved values on its stdin envelope. Do NOT make
    `score.py` read `.vibe-check.toml` itself.
  - **Precedence (CONFIG-02):** the helper (or the orchestrator around it) resolves
    CLI flag > toml value > built-in default per knob. For Phase 30's three
    consumers, only the toml-vs-default layer must work end-to-end; the flag layer
    is exercised more heavily by later phases (`--min-confidence`, `--codex`), but
    the precedence mechanism is established here.

### Warning verbosity & placement
- **D-04:** Per-key fail-safe warnings surface as **one dedicated "config-health"
  line near the top of the report** (e.g. `⚠ config: <key> invalid (<reason>) —
  using default`), NOT inline on each finding and NOT scattered. Multiple invalid
  keys aggregate onto that one config-health block. Loud enough to never silently
  drop a misconfiguration (the project's "never silently drop" principle), but it
  does not clutter the per-finding output. An absent file produces NO warning (the
  common zero-config case — CONFIG-01 back-compat).

### Claude's Discretion (planner/executor owns these)
- Exact helper filename/module layout and function signatures.
- Exact envelope key name for `thresholds` and its JSON shape.
- Exact warning-line wording and the config-health block format.
- Which `band_for` literal each `thresholds` sub-key maps to (within D-02's
  constraint that the default path stays byte-stable).
- README schema-doc layout (CONFIG-04 requires the schema documented; format is
  open).
</decisions>

<specifics>
## Specific Ideas

- Mirror the `score.py` resolution precedent (review.md step 3): working-tree-first
  / cache-fallback / fail-closed-if-absent — the config helper and its `.vibe-check.toml`
  read should follow the same dev-safe resolution posture so dev runs read the
  working-tree config, not a stale cache.
- The zero-config common case must be SILENT and behaviorally identical to v2.7 —
  no warning, no banner, no behavior change. This is CONFIG-01 and the milestone's
  back-compat anchor.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone design (authoritative)
- `docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md` — the
  approved v2.8 design spec. §1 (six deliverables + illustrative schema), §2
  (architecture: who-reads/who-enforces table + precedence + the load-bearing
  per-key fail-safe), §3 (Phase 30 = config surface foundation), §4 (testing +
  definition of done), §5 (out-of-scope — formula rewrite forbidden).
- `.planning/ROADMAP.md` — Phase 30 detail block (Success Criteria 1-5) and the
  v2.8 "Phase Details" preamble.
- `.planning/REQUIREMENTS.md` — CONFIG-01..04 acceptance criteria (lines 14-17).

### Code surfaces this phase touches
- `plugins/vibe-check/scripts/score.py` — `band_for()` (line 86, the band-boundary
  literals `thresholds` parameterizes), `THRESHOLDS` (line 44, the per-command
  cutoff that is NOT tuned), `run(envelope)` (line 668, where new envelope keys are
  consumed), the pure-function boundary doc (lines 8-17).
- `plugins/vibe-check/scripts/test_score.py` — the established unit-test pattern;
  new `thresholds` envelope-key cases + the default-path byte-stability regression
  lock land here.
- `plugins/vibe-check/commands/review.md` — envelope build + score.py invocation
  (step 3-4, ~lines 697-743); top-model resolution (`$VIBE_CHECK_TOP_MODEL`, line
  553); where the config read + dispatch-knob enforcement wires in.
- `plugins/vibe-check/commands/deep-review.md` — delegates review.md's scoring
  Phase verbatim; check whether any config wiring needs a parallel touch.
- README (repo or plugin) — CONFIG-04 requires the `.vibe-check.toml` schema
  documented (`[review]`/`[agents]`/`[noise]` sections, keys, defaults).

### Prior-art precedents (read for pattern, not requirement)
- The framework-skill `≤45` low-tier ceiling — the category-aware capping pattern
  that `idiom_floor` reuses in Phase 32 (not this phase, but confirms the capping
  mechanism `thresholds`-style envelope keys ride).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `score.py`'s stdin→stdout JSON envelope (`run(envelope)`, line 668) — the
  established orchestrator→script boundary. New script-enforced knobs become
  additive envelope keys; the diff-mode envelope shape stays back-compatible when a
  key is absent (the existing `envelope.get(key, default)` pattern).
- `score.py`'s dev-safe resolution + fail-closed `__main__` (review.md step 3) —
  the precedent for how the new config helper should resolve its file path and fail
  safely.
- `test_score.py` — the unit-test harness (run via `python3 -m unittest` per
  `.orchestrator.json` `test_verify_cmd`, workdir `plugins/vibe-check/scripts`).

### Established Patterns
- Pure-function `score.py` boundary: NO filesystem/git/shell I/O inside the script;
  every fact arrives pre-resolved on stdin. The config helper is the I/O boundary;
  `score.py` stays pure (D-03 boundary note).
- "Never silently drop" — warnings are loud but non-fatal (mirrors the existing
  missing-config → defaults posture).
- Single-writer for scored fields — `score.py` is the only writer of
  `band`/`orchestrator_score`/`status`/`stable_hash`. Adding `thresholds` must not
  introduce a second banding path.

### Integration Points
- Orchestrator reads config helper → passes `thresholds` into the `score.py`
  envelope (script-enforced) and applies `disabled`/`top_model` at dispatch
  (orchestrator-enforced), per the design-spec §2 enforcement table.
- `band_for()` switches from hardcoded literals to reading the envelope-supplied
  `thresholds` (defaulting to today's literals when the key is absent).
</code_context>

<deferred>
## Deferred Ideas

- `min_confidence` / `--min-confidence N` confidence-axis filter — **Phase 31**.
- `idiom_floor` band cap + `// vibe-ignore: <reason>` marker — **Phase 32**.
- Codex `off/auto/on` legibility + safer fix-loop default — **Phase 33**.
- gitleaks (999.2), SARIF (999.3), PR-posting (999.5), measured cost (999.12),
  docs pass (999.13) — out of v2.8 entirely (spec §5).
- Rewriting the scoring formula / re-deriving `agent_confidence` — explicitly
  forbidden (spec §5). `thresholds` parameterizes; it does not re-weight.
</deferred>

---

*Phase: 30-config-surface-foundation*
*Context gathered: 2026-06-30*
