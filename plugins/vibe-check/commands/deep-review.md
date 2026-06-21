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
