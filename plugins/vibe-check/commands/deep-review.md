---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Edit, Grep, Glob, Task, AskUserQuestion, Bash(node:*)
description: Deep comprehensive code review with full context analysis
---

## HARD CONTRACT (read this before doing anything)

This command is an **orchestrator** — its sole job is to execute the phases below in order. The phases are NOT optional, NOT a menu, and NOT a template for inspiration. If you find yourself "skipping ahead to the report" or "improvising a summary file," STOP — that is a failure mode. Follow the prose step-by-step, in numerical phase order, top to bottom.

**Output paths — non-negotiable:**

- **WRITE only to `.turingmind/`** in the user's project. Specifically: `.turingmind/state/<id>.json` (Phase 4.5), optional `.turingmind/reviews/<timestamp>/` (Phase 4.5 snapshot), and `.turingmind/REVIEW.md` (only via Finalize mode).
- **NEVER write to `.planning/`** — that namespace belongs to GSD. The tool READS PLAN.md/SPEC.md/RESEARCH.md from there (Phase 1.5) but writes nothing.
- **NEVER write per-phase review files** like `.planning/phases/<id>/<NN>-REVIEW.md` or `<NN>-DEEP-REVIEW.md` even if you see GSD/other plugins creating files in that location. **This tool does not produce per-phase artifacts in `.planning/`.** The single authoritative artifact is `.turingmind/REVIEW.md`, written by `--finalize`.
- Mid-loop `/review` and `/deep-review` invocations **print findings to the chat transcript only**. No file write of the report itself. State file under `.turingmind/state/` is the only thing persisted by a non-finalize pass.

**Phase progression — non-negotiable:**

- Announce each phase as you enter it with one line: `✓ Phase N — <name>` (or `⊘ Phase N — <name> (skipped: <reason>)`). The user reads these announcements to verify the orchestrator is on track.
- Phase 4 (Render) MUST be followed by Phase 4.5 (Persist state). Phase 4.5 MUST be followed by Phase 5 (Interactive fix loop) UNLESS one of Phase 5's documented skip conditions applies.
- "I already rendered the report so I'm done" is the failure mode — Phase 5 is part of the user-facing contract, not a polish step.

**If unsure, surface the uncertainty rather than improvise.** Print "I'm uncertain about <specific phase or step> — orchestrator prose is ambiguous here" and stop.

---

Comprehensive review with architecture + impact analysis + intent-doc alignment. Use for pre-PR or final-pass review.

## Phase contract — how /deep-review composes with /review

**You MUST read `commands/review.md` to get the full phase specs for Phase 0, 0.5, 0.7, 1, 1.5, 3, 4, 4.5, 5, and Finalize mode.** Don't infer from the section titles below — read the source.

Concretely, your execution order is:

1. Read `commands/review.md` end-to-end (it lives next to this file under `plugins/vibe-check/commands/review.md`). That file is the authoritative spec for the shared phases AND for the HARD CONTRACT above (which applies identically to `/deep-review`).
2. Execute Phase 0, 0.5, 0.7, 1, 1.5 per `commands/review.md`.
3. Execute Phase 2 (agent selection) per the "Differences from /review" section below — this command DIFFERS from `/review` in agent dispatch (adds architecture+impact, lowers threshold). Use the table in "Differences" below, NOT the Phase 2 table in `commands/review.md`.
4. Execute Phase 1c (Related files) per "Differences" below — this is a NEW phase that /review doesn't have.
5. Execute Phase 2.5 (Architecture prompt enhancement) per "Differences" below.
6. Execute Phase 3, 4, 4.5 per `commands/review.md` — Phase 4 picks up extra rendering for Architectural Notes + Impact Analysis per "Differences" below.
7. Execute Phase 5 (Interactive fix loop) per `commands/review.md` verbatim — when the loop's "rerun" option fires, it re-enters `/deep-review` (this command), not `/review`. When "close out" fires, it routes to Finalize mode per `commands/review.md`.
8. Finalize mode (if --finalize in $ARGUMENTS) is the same as `commands/review.md` Finalize mode, verbatim.

**Phase 5 is not optional for /deep-review either.** The HARD CONTRACT above applies. If you skip Phase 5, you've violated the contract.

## Differences from /review

### Phase 2 — agent selection (deep adds architecture + impact)

**Top-tier model resolution (do this first, once per run).** Read the env var `$VIBE_CHECK_TOP_MODEL`. If it is set to a non-empty value, that is `<TOP>` (e.g. `fable`). If unset or empty, `<TOP>` defaults to `opus`. Use `<TOP>` wherever the table below says **top** below. Only `opus` and `fable` are supported values; if it's set to anything else, fall back to `opus` and tell the user once: "⚠ Unrecognized $VIBE_CHECK_TOP_MODEL — using opus." Do NOT print anything when it resolves normally.

| Always | Condition | Agent | Model |
|--------|-----------|-------|-------|
| ✓ | — | `bugs` | **top** (per-call override) |
| ✓ | — | `security` | sonnet |
| ✓ | — | `architecture` | **top** (per-call override) |
| ✓ | — | `impact` | opus (frontmatter) |
|  | `CLAUDE.md`/`AGENTS.md` exists | `compliance` | sonnet |
|  | TS/JS in diff | `language-typescript` | sonnet |
|  | Python in diff | `language-python` | sonnet |
|  | Go in diff | `language-go` | sonnet |
|  | Rust in diff | `language-rust` | sonnet |
|  | React imports | `framework-react` | sonnet |
|  | FastAPI imports | `framework-fastapi` | sonnet |

**Why the top tier on `bugs` and `architecture`:** these are the two agents whose judgment gates what ships — missed real bugs and intent-vs-implementation drift are the costliest failure modes, and each is a single dispatch per pass so the upgrade cost is bounded. `bugs` keeps `model: sonnet` in its frontmatter (that's what `/review` uses for cheap iteration); `/deep-review` upgrades it by passing `model: "<TOP>"` in the Task call — the same per-call override mechanism as the large-diff Haiku downgrade in `commands/review.md` M5. `architecture` defaults to `opus` in its frontmatter but `/deep-review` likewise passes `model: "<TOP>"` per-call so the env var governs it too. `impact` is deep-only and stays on `opus` via its frontmatter — no override.

**Default is Opus; Fable is opt-in.** Out of the box `<TOP>` is `opus`, which every paid tier can reach with no retry delay. Users whose subscription includes Fable can set `VIBE_CHECK_TOP_MODEL=fable` to upgrade the two gating agents to the strongest tier. See the README's Configuration section.

**Do NOT pass any thinking parameter in Task calls.** `thinking_budget` is not a Task-tool parameter, and fixed thinking budgets are deprecated API-wide — both Opus and Fable think adaptively on their own. The model choice in the table above is the reasoning-depth lever; there is nothing else to set.

### Phase 1c — Related files (for impact agent)

After Phase 1.5, before Phase 2, for impact agent only:

For each diff file:
- `git grep -l "from.*<basename>"` → importers
- Parse diff's import statements → importees
- Find test files: `<basename>.test.*`, `test_<basename>.*`, `__tests__/<basename>.*`

Assemble `<related-files>`:

```
<related-files>
  <file path="src/users.ts">
    <imported-by>src/api/handlers.ts, src/admin/routes.ts</imported-by>
    <imports>src/db/client.ts, src/lib/email.ts</imports>
    <test-file>src/users.test.ts</test-file>
  </file>
</related-files>
```

Inject into impact agent's prompt only.

### Phase 2.5 — Architecture prompt enhancement

Architecture prompt includes `<intent-context>` AND the related-files block:

```
You are the architecture agent. Reason deeply about cross-file implications, intent alignment, pattern consistency.

{{intent-context}}

<diff>
{{git_diff}}
</diff>

<related-files>
{{from Phase 1c}}
</related-files>
```

### Phase 2b — Collection-mechanism smoke-check (one-time tool-viability gate, run BEFORE Phase 2c relies on background collection)

The Codex pass is launched as a backgrounded shell in Phase 2c and **collected** in Phase 3 by reading that shell's output. Under the self-contained-watchdog design (Phase 2c), the launched shell **self-kills** the codex process at the cap and emits its own timeout sentinel, so the orchestrator never needs to kill the shell — `KillShell` is **NOT on the critical path**. The collection mechanism therefore depends on exactly **one** built-in tool being callable from this command's context: **`BashOutput`**. The smoke-check is **`BashOutput`-only** by design.

**This is a REAL EXECUTION gate, not a prose claim. The executor MUST actually run it once during verification, before trusting background collection:**

1. Launch a trivial command via `Bash(run_in_background: true)` that prints the fixed sentinel: `echo __SMOKE_OK__`. Capture the returned `shell_id`.
2. Read that backgrounded shell back with `BashOutput(shell_id)`.
3. **PASS** the gate iff the `BashOutput` read is available AND the returned output contains the literal sentinel `__SMOKE_OK__`.
4. **FAIL CLOSED** otherwise. If `BashOutput` is not callable from this command's context, or the read returns no output, that is a **structural blocker** that **blocks completion NOW** — do not defer it to a later live run. Without a working `BashOutput` read the Codex job can be launched but never collected, silently degrading to native-only and violating SAFE-02. On fail, surface the blocker and stop; do not proceed as if Codex collection works.

Record the smoke-check result (PASS/FAIL, and that `__SMOKE_OK__` was observed) in the run's evidence. `BashOutput`/`KillShell` are Claude Code **built-ins** and are **not** added to `allowed-tools` (only `Bash(node:*)` is). This probe edits no source — it just runs `echo` and reads it back — so it stays fully within the prompt-only + files-touched constraints; it is never a committed code/test artifact.

> A live **authenticated** probe→launch→collect against real Codex is deferred to the efficacy phase (Phase 6, EFF-01). The `BashOutput` **callability** smoke-check above is NOT deferred — it is a structural gate run here with a trivial `echo` (no Codex auth required).

### Phase 2c — Codex kickoff (probe + launch)

**Run this as its OWN turn(s) BEFORE the Phase 2 native fan-out turn. It is text + Bash only — it never adds a tool call to the pure-Task Phase 2 turn.** Phase 2's **MANDATORY DISPATCH SHAPE** (`commands/review.md`: one assistant turn = exactly N parallel `Task` calls, zero other tool calls) forbids any non-Task tool call in that turn, so the probe/launch Bash MUST live in a prior turn. Codex is a separate orchestrator-run step launched here and **collected at Phase 3** — never one of the parallel `Task` calls.

**Two corrections baked in (do NOT revert them to older wording).** Probe with `setup --json` and gate on `.ready == true` — **NOT** `status --json` (which exits 0 even when Codex is uninstalled/logged-out and checks no auth, so it cannot gate). Background the launch with Claude Code `Bash(run_in_background: true)`, **NOT** the companion's `--background`/`--wait` (which `adversarial-review` ignores — it always foregrounds and prints no job-id). The 300s cap is enforced by a self-contained watchdog **INSIDE** the backgrounded command, not by orchestrator poll timing.

In order:

1. **Resolve `${CODEX_PLUGIN_ROOT}` (versioned-cache glob → `sort -V` → marketplace fallback → not-installed guard).** Author this fresh (no in-repo analog). The cache path nests under `…/codex/<version>/`, so the glob is two levels:
   ```bash
   CODEX_PLUGIN_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/openai-codex/codex/*/ 2>/dev/null | sort -V | tail -1)
   CODEX_PLUGIN_ROOT="${CODEX_PLUGIN_ROOT%/}"
   if [ -z "$CODEX_PLUGIN_ROOT" ] || [ ! -f "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" ]; then
     CODEX_PLUGIN_ROOT="$HOME/.claude/plugins/marketplaces/openai-codex/plugins/codex"
   fi
   if [ ! -f "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" ]; then
     echo "__CODEX_NOT_INSTALLED__"   # → skip-and-note, native-only (reason slug: not-installed)
   fi
   ```

2. **Probe + GO/skip gate (RESEARCH CORRECTION 1).** Run `node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" setup --json`. **GO** iff exit 0 AND stdout parses AND `.ready == true` (≡ `.codex.available == true && .auth.loggedIn == true`). **NOT-GO** → print the one skip-and-note line, set a `CODEX_SKIPPED` marker, do **not** launch (Phase 3 collect becomes a no-op). NOT-GO triggers, all converging on the one skip line (only the `<reason>` slug varies): non-zero exit (`unavailable`); unparseable JSON (`unavailable`); `.ready == false`; `.codex.available == false` (`not-installed`); `.auth.loggedIn == false` (`unauthenticated`). `setup --json` is read-only (no flags), so it is side-effect-free as a probe.

3. **Disclosure line (CODEX-04) — print ONCE at kickoff, as text (not a tool call, not per poll):**
   `▶ Running Codex adversarial review in parallel (GPT-5-codex, ~1–3 min, deep-review only)…`

4. **Diff-targeting — ONE GENERAL, mode-agnostic RULE (stated FIRST), then every mode as a CONSEQUENCE.** This is the load-bearing gate; do **not** write four independent per-mode branches.

   **The general rule.** Run Codex ONLY when Codex's **representable review range** can be shown to **EXACTLY EQUAL** the Phase-0-resolved diff set for the active mode. Codex can represent exactly **two** ranges: `--scope working-tree` (= the uncommitted working tree: staged + unstaged + untracked) and `--base <ref> --scope branch` (= `merge-base(HEAD,<ref>)..HEAD`, **COMMITTED ONLY**, always diffed against HEAD). It has **no** way to represent an arbitrary non-ancestor left boundary, a right side ≠ HEAD, or the **UNION** of a committed range PLUS a dirty (staged/unstaged) tail. If neither representable range provably equals the mode's Phase-0 diff, **FAIL CLOSED**: emit the skip-and-note line, set `CODEX_SKIPPED`, do **not** launch, run native-only — Codex never reviews a partial or different diff. **Skip-and-note-on-non-representable-diff is the DEFAULT/fallback for ANY mode — including future modes — whose Phase-0 diff Codex cannot exactly represent.** Why this matters: the later Phase 3 step-2 `in_diff` clip can drop EXTRA (out-of-diff) Codex findings but **cannot recover defects Codex never reviewed**, so a non-representable range would silently miss real defects while CODEX-01 looked satisfied (a wrong/partial diff). Tie to SAFE-01: a Codex limitation degrades to a clean skip, never a silent wrong/partial review, and never blocks the native review.

   **Each mode is a CONSEQUENCE of the one rule (not a separate special case):**
   - **default mode** — Phase-0 diff IS the uncommitted working tree → `--scope working-tree` (omit `--base`) represents it EXACTLY → **RUN**. The **identity** case; no dirty/committed mismatch is possible.
   - **GSD phase mode, empty `PHASE_RANGE`** (`review.md` Phase 0 fallback) — Phase-0 diff = staged + unstaged only = the working tree → `--scope working-tree` → **RUN**.
   - **GSD phase mode, non-empty `PHASE_RANGE` AND a CLEAN working tree (no staged/unstaged) AND `$PHASE_START` is an ANCESTOR of HEAD** (i.e. `git merge-base HEAD "$PHASE_START"` == `git rev-parse "$PHASE_START"`, so `merge-base(HEAD,$PHASE_START)==$PHASE_START`) — Phase-0 diff = exactly `$PHASE_START..HEAD` → `--base "$PHASE_START" --scope branch` represents it exactly → **RUN**.
   - **GSD phase mode, non-empty `PHASE_RANGE` AND there ARE staged/unstaged changes** (Phase-0 diff = the committed range `$PHASE_START..HEAD` PLUS a dirty tail; Codex branch mode reviews ONLY the committed range and OMITS the tail, and working-tree mode reviews ONLY the tree and omits the committed range — Codex can represent NEITHER the union NOR exactly either part) → **FAIL CLOSED: skip-and-note native-only** (reason slug `phase-diff-has-uncommitted-tail`). This is the COMMON in-progress case (a phase with uncommitted edits). *(DEFERRED future enhancement: a mechanism that hands Codex the full committed+dirty union — note it, do NOT implement.)*
   - **PR mode / range mode** — `--base <base-ref> --scope branch`, run ONLY if `merge-base(HEAD,base)..HEAD` provably EQUALS the resolved Phase-0 diff — the FULL comparison boundary, BOTH the upper ref AND the base/left-ref identity, NOT just `HEAD == upper-ref`:
     - **Range mode `A..B`** (`/review` resolves the LITERAL two-dot `A..B`): require BOTH (i) `git rev-parse HEAD` == `git rev-parse <B>` (the upper ref), AND (ii) `A` is an **ANCESTOR** of `B`, i.e. `git merge-base HEAD <A>` (== `merge-base(B,A)`) equals `git rev-parse <A>` — so Codex's `merge-base(HEAD,A)..HEAD` is exactly the literal `A..B`. If `A` is NOT an ancestor of `B`, Codex would review `merge-base(B,A)..B` → **FAIL CLOSED** (slug `range-not-identical`).
     - **PR mode** (`gh pr diff <ref>`): require `git rev-parse HEAD` == the **PR head SHA** AND that the local merge-base against the PR base (`git merge-base HEAD <pr-base>`) equals the PR's ACTUAL diff base (the head/base `gh pr view <ref> --json` reports). If local HEAD != PR head OR the local merge-base against the PR base != the PR's diff base (e.g. a stale/mismatched local base ref) → **FAIL CLOSED** (slug `head-not-at-target`).

   **On ANY mode whose representable-range==Phase-0-diff check fails — or cannot be cheaply verified — FAIL CLOSED** (emit the skip-and-note line with the appropriate reason slug, set `CODEX_SKIPPED`, do not launch, run native-only). This ties CODEX-01 to the FULL right diff uniformly: Codex runs ONLY when its representable range provably equals the orchestrator's resolved Phase-0 diff, or it transparently skips — never a silent wrong/partial diff. `--base` is always the orchestrator's OWN resolved ref (D-08), NEVER derived from Codex output, and `--base <ref>` forces branch mode regardless of `--scope`. **This tightens D-04/D-05 from "best-effort superset/subset with the `in_diff` safety net" to "EXACT-or-skip"** — a deliberate, strictly safer enforcement consistent with the locked intent (skip-and-note is the SAFE-01 posture); the `in_diff` override (D-05) remains defense-in-depth on the RUN paths but is no longer relied on to paper over a partial/wrong range. *(DEFERRED future enhancement: a temp-worktree checkout of the target head — which would also let Codex review a literal non-ancestor `A..B` AND a committed+dirty union — note it, do NOT implement here.)* The PR/range `merge-base` base-ref-must-exist-locally degradation is expected (→ skip-and-note), not a bug.

5. **Background launch with a SELF-CONTAINED 300s watchdog (RESEARCH CORRECTION 2).** Only reached on a RUN mode (a skip-and-note mode never launches). Record `started_at` (`date +%s`) at this kickoff. Make ONE `Bash(run_in_background: true)` call whose COMMAND wraps the codex invocation so the cap is enforced by the launched shell ITSELF, independent of when the orchestrator next polls. The single named constant is **`CODEX_TIMEOUT_SECONDS = 300`** (one named value, not scattered magic numbers). The background command must: (a) run `node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" adversarial-review --json --base "$BASE" --scope "$SCOPE"` in the background of that shell, capturing its PID (for working-tree mode omit `--base` and pass `--scope working-tree`); (b) run a watchdog bound (`sleep 300; kill <pid>` style, or `timeout 300`/`gtimeout 300` if available) so that at `CODEX_TIMEOUT_SECONDS` the codex process is killed and the shell emits the stable **timeout sentinel** `__CODEX_TIMEOUT__` on stdout before exiting; (c) on normal completion within the cap, print the codex `--json` payload to stdout and exit 0. Capture the returned shell id for the Phase 3 collect step.
   ```bash
   # ONE run_in_background:true call. CODEX_TIMEOUT_SECONDS=300 (single named value).
   # RUN-mode branch + scope already resolved above ($BASE/$SCOPE; omit --base for working-tree).
   ( node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" adversarial-review --json \
       --base "$BASE" --scope "$SCOPE" & CODEX_PID=$!
     ( sleep 300; kill "$CODEX_PID" 2>/dev/null; echo __CODEX_TIMEOUT__ ) & WD_PID=$!
     wait "$CODEX_PID" 2>/dev/null; kill "$WD_PID" 2>/dev/null )
   ```
   **The 300s ceiling is enforced by the background command's own watchdog, so a hung Codex self-terminates at `CODEX_TIMEOUT_SECONDS` even if the orchestrator does not poll for minutes** — the cap holds independent of poll timing; the orchestrator's later `BashOutput` read just observes the result-or-sentinel. *(If a fully self-contained `kill`/`timeout` watchdog were genuinely not expressible in this command's Bash surface, state SAFE-02 honestly as "max ADDITIONAL wait measured from collection start is 300s" and gate on `(now - started_at) >= CODEX_TIMEOUT_SECONDS` — but the self-contained watchdog above is REQUIRED unless that impossibility is documented.)*

### Phase 3 — Filter threshold

Use ≥70 (Critical + Warning + Medium) instead of ≥80.

### Phase 4 — Output

In addition to standard sections:

```markdown
### Architectural Notes 📐
{{architecture's agent_notes as bullets}}

### Impact Analysis 💥
{{impact's agent_notes as bullets}}
- **Files affected:** {{count from related-files}}
- **Breaking changes detected:** {{yes/no based on impact findings with category=breaking-api}}
```

### Phase 4.5 — State

`mode: "deep"` in pass entry.

### --finalize

Same flow as review.md.

## Cost note

Typical deep pass ~$2–4 (the top-tier model on `architecture` + `bugs` is the driver). On the default Opus tier that's roughly the low end; opting up to Fable (`VIBE_CHECK_TOP_MODEL=fable`) raises it — Fable is ~2× Opus and ~3.3× Sonnet per token. Use sparingly — final pass before PR/finalize. Mid-loop should use `/review`.
