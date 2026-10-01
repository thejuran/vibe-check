# Phase 2 — Deep agent selection (deep adds architecture + impact + test-sufficiency)

> **Lazy-loaded.** Read from `commands/deep-review.md` when Phase 2 is entered (every deep review), together with `$VC_ROOT/phases/review/20-dispatch.md`, in the pre-dispatch turn.
> This table REPLACES the Selection table in `20-dispatch.md` for WHICH agents fire; `20-dispatch.md` (and, in `--all`, `20-dispatch-all.md`) still governs HOW they are dispatched. Announce `✓ Phase 2 — Dispatching N agents in parallel: [list]` in the dispatch turn, after both Reads.

**`--all` mode (`$ALL_MODE` set) — this table is applied PER CHUNK inside the per-chunk dispatch loop (Site C, `$VC_ROOT/phases/review/20-dispatch-all.md`).** In `--all`, deep Phase 2 does NOT do a single whole-set dispatch: it runs the per-chunk loop in `20-dispatch-all.md` (one chunk at a time, riskiest first — D-05), and for EACH chunk this deep table selects that chunk's agents. `architecture` + `impact` JOIN EACH chunk's agent set (alongside `bugs`/`security` always + `language-*`/`framework-*` selected from THAT chunk's per-chunk triage + `compliance` when `CLAUDE.md`/`AGENTS.md` is present), and each chunk's deep agents are dispatched in that chunk's ONE pure-Task fan-out turn over `$FILES_BLOCK_i` (D-04/D-05/D-08 — position-stable within the chunk). Responses accumulate into `$AGENT_RESPONSES`; Phase 3 runs ONCE after the loop. So `/deep-review --all` produces chunk-numbered output exactly like `/review --all` (each chunk's report adds architecture+impact), NOT a single-unit deep report. The model-tiering table and prose below are UNCHANGED — they govern WHICH agents and at WHAT model tier, applied per chunk.

**Top-tier model resolution (do this first, once per run) — precedence `env > toml > default(opus)` (CONFIG-02).** Resolve `<TOP>` in this order:
1. **`$VIBE_CHECK_TOP_MODEL` (env — WINS, the flag tier).** If it is set to a non-empty value, that is `<TOP>` (e.g. `fable`) — a power user's shell override beats a repo config.
2. **config `top_model` (toml).** Else, if the carried-forward `$CONFIG_TOP_MODEL` (resolved ONCE in Phase 0.6 — NOT a re-read) is a non-empty value, that is `<TOP>`. `config.py` already validated the toml value to `opus`/`fable`/None, so a None `$CONFIG_TOP_MODEL` (absent or invalid in the toml) simply falls through to the default below.
3. **`opus` (default).** Else `<TOP>` defaults to `opus`.

Use `<TOP>` wherever the table below says **top**. Only `opus` and `fable` are supported values; if EITHER source resolves to anything else, fall back to `opus` and tell the user once — `"⚠ Unrecognized $VIBE_CHECK_TOP_MODEL — using opus."` for a bogus env var, or `"⚠ Unrecognized top_model in .vibe-check.toml — using opus."` for a bogus toml value — reusing the SAME `opus`/`fable` allowlist + fallback-to-opus + one-time warning for BOTH sources so the env var and the toml key cannot diverge (Pitfall 6). Do NOT print anything when it resolves normally.

| Always | Condition | Agent | Model |
|--------|-----------|-------|-------|
| ✓ | — | `bugs` | **top** (per-call override) |
| ✓ | — | `security` | sonnet |
| ✓ | — | `architecture` | **top** (per-call override) |
| ✓ | — | `impact` | opus (frontmatter) |
| ✓ | — | `test-sufficiency` | opus (frontmatter) |
|  | `CLAUDE.md`/`AGENTS.md` exists | `compliance` | sonnet |
|  | TS/JS/.vue in diff | `language-typescript` | sonnet |
|  | Python in diff | `language-python` | sonnet |
|  | Go in diff | `language-go` | sonnet |
|  | Rust in diff | `language-rust` | sonnet |
|  | React imports | `framework-react` | sonnet |
|  | FastAPI imports | `framework-fastapi` | sonnet |
|  | "skill" (`SKILL.md` / agent `.md` / plugin manifest) | `framework-skill` | sonnet |
|  | Express imports | `framework-express` | sonnet |
|  | Vue imports / `.vue` SFC | `framework-vue` | sonnet |
|  | Angular imports | `framework-angular` | sonnet |
|  | Electron imports | `framework-electron` | sonnet |
|  | React Native imports (triage.frameworks "react-native") | `framework-react-native` | sonnet |

**Subtract `$CONFIG_DISABLED` from THIS deep Selection set BEFORE dispatch (config `disabled` → dispatch, parallel to `/review`'s `20-dispatch.md`).** The `disabled` roster was ALREADY resolved ONCE in Phase 0.6 (carried as `$CONFIG_DISABLED`) — deep-review does NOT re-read `config.py`; it consumes the carried-forward var. After this deep table produces its selected agent set (which adds `architecture`+`impact`+`test-sufficiency` to the universal floor; in diff mode `test-sufficiency` is subject to the coverage gate below) and BEFORE the dispatch announcement / fan-out, REMOVE any agent whose name ∈ `$CONFIG_DISABLED` from the set, so the disabled agents never dispatch and `score.py` never sees them. **Same LOCKED policy as `/review`:** HONOR any disable including a core agent (`bugs`/`security`); when `bugs` or `security` is disabled, APPEND the fixed-string `⚠ config: core agent '<name>' disabled — coverage reduced` announcement to the Phase-4 config-health warnings (never silent). A disabled deep-only agent (`architecture`/`impact`/`test-sufficiency`) or non-core agent is subtracted silently. In `--all` mode the subtraction applies inside EACH chunk's per-chunk deep fan-out (Site C) the same way (the roster is run-level). **Nothing else in config needs a deep-only touch:** `thresholds`, `min_confidence`, `idiom_floor`, the `// vibe-ignore` marker, and the Suppression (audit) and Low / Informational renders are resolved at Phase 0.6 (`06-config.md`) and applied at Phase 3 (`30-collect-score.md`) and Phase 4 (`40-render.md`) — the same shared files `/review` reads — so `/deep-review` adds NO config read and NO envelope key of its own. Only `top_model` and `disabled` are consumed here.

**DIFF-MODE COVERAGE GATE — remove `test-sufficiency` AFTER the `$CONFIG_DISABLED` subtraction and BEFORE the dispatch announcement (GATE-01).** The Selection table above is the candidate set and stays as it is; this paragraph is the ONE place `test-sufficiency` is removed on evidence. Apply the steps in order. Step 1: apply the table. Step 2: subtract `$CONFIG_DISABLED` (the paragraph above). Step 3, the single gating step, has two inseparable effects. If `test-sufficiency` was already subtracted in step 2 (`test-sufficiency` ∈ `$CONFIG_DISABLED`), the gate is NOT consulted and `$TS_GATED` stays unset: disabled wins, and the lane is subtracted exactly once. Otherwise, if the carried `$TS_GATE_CASE` (bound by Phase 1d, `01d-coverage.md`) is `no-artifact` or `none-usable`, REMOVE `test-sufficiency` from the set AND bind `$TS_GATED=<that case>` in that same step. There is never a removal without `$TS_GATED`, and never a `$TS_GATED` without a removal; the optional announce suffix and the Phase 4 note both key off it. Step 4: announce. This is a REQUIRED OUTPUT on every deep run, gated or not: print the `✓ Phase 2 — Dispatching N agents in parallel: [list]` line exactly once, as text in the dispatch turn before the Task calls, followed by the `✓ Phase 2.5 — Architecture prompt enhancement` line. Gating changes only the line's suffix, never whether the line prints; dispatching without the line is a defect. `N` and `[list]` already reflect BOTH subtractions, so `N` is exactly one fewer than the table would otherwise produce when the lane is gated, and unchanged when the block is non-empty. When `$TS_GATE_CASE` is `present` or UNSET (the helper failed, `$VC_ROOT` was empty, or the run is `--all`), dispatch exactly as today. An unset case is NEVER read as empty. The announce stays ONE line with its existing prefix. The Phase 1d status line (`01d-coverage.md`) is the single required statement of the gate outcome; the suffix below is OPTIONAL and best-effort, an echo of that line, and omitting it is not a defect. When a suffix is appended, it is this fixed wording for the case:

- `no-artifact` -> `✓ Phase 2 — Dispatching N agents in parallel: [list] — test-sufficiency not dispatched: no coverage artifact found`
- `none-usable` -> `✓ Phase 2 — Dispatching N agents in parallel: [list] — test-sufficiency not dispatched: coverage artifacts found, none usable for the changed files`

Never put this on a separate line that starts with the skip glyph followed by `Phase 2`: tracecheck reads such a line as the whole phase being skipped. The suffix is chat text, never prompt content, and it names no path, file name or rejection reason. Disabled wins silently: if `test-sufficiency` ∈ `$CONFIG_DISABLED`, the gate is not consulted, `$TS_GATED` stays unset, no suffix is appended and no note renders. In `--all` (`$ALL_MODE` set) `$TS_GATE_CASE` is never bound and this paragraph does not apply; per-chunk selection is unchanged (D-03).

**Why the top tier on `bugs` and `architecture`:** these are the two agents whose judgment gates what ships — missed real bugs and intent-vs-implementation drift are the costliest failure modes, and each is a single dispatch per pass so the upgrade cost is bounded. `bugs` keeps `model: sonnet` in its frontmatter (that's what `/review` uses for cheap iteration); `/deep-review` upgrades it by passing `model: "<TOP>"` in the Task call — the same per-call override mechanism as the large-diff Haiku downgrade in `20-dispatch.md` M5. `architecture` defaults to `opus` in its frontmatter but `/deep-review` likewise passes `model: "<TOP>"` per-call so the env var governs it too. `impact` is deep-only and stays on `opus` via its frontmatter — no override.

**Default is Opus; Fable is opt-in.** Out of the box `<TOP>` is `opus`, which every paid tier can reach with no retry delay. Users whose subscription includes Fable can set `VIBE_CHECK_TOP_MODEL=fable` to upgrade the two gating agents to the strongest tier. See the README's Configuration section.

**Do NOT pass any thinking parameter in Task calls.** `thinking_budget` is not a Task-tool parameter, and fixed thinking budgets are deprecated API-wide — both Opus and Fable think adaptively on their own. The model choice in the table above is the reasoning-depth lever; there is nothing else to set.

### Phase 1c — Related files (for impact agent)

After Phase 1.5, before Phase 2, for impact agent only:

For each diff file:

## Filter threshold (applied at Phase 3)

Use ≥70 (Critical + Warning + Medium) instead of ≥80. `score.py` applies it from the envelope's `command: "deep-review"`; this is the rule it implements, stated here because it decides which Medium findings a deep review surfaces.

**Phase 10 `--all` deep-Medium render narrowing (OUTPUT-01/02, D-02).** The ≥70 filter threshold above is INTENTIONALLY left unchanged — `/deep-review` still SCORES and COUNTS Medium at ≥70. In plain `--all`, `/deep-review`'s default Critical+Warning listing comes from the `$ALL_MODE && !--full` RENDER-time listing bar in `$VC_ROOT/phases/review/40-render-all.md` (Plan 10-01, Phase 4), which narrows deep's default-Medium back to C+W at `render` (output-format.md lists Medium as shown for Deep, so without this render narrowing `/deep-review --all` would default to showing Medium) — so Medium is counted-not-listed in plain `--all`, and `--all --full` reveals the Medium section. Do NOT lower the ≥70 threshold to narrow `--all` (D-02 forbids threshold changes — narrow at `render`, not at the threshold).
