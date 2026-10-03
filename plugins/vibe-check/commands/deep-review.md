---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Edit, Grep, Glob, Task, AskUserQuestion, Bash(node:*)
description: Deep comprehensive code review with full context analysis
---

Comprehensive review with architecture + impact analysis + intent-doc alignment. Use for pre-PR or final-pass review.

This command is an **orchestrator**. It runs the review phases listed below, in order. Each phase's full instructions live in their own file under the plugin's `phases/` directory and are loaded only when that phase runs. The phases `/deep-review` shares with `/review` are the SAME files `/review` reads; the deep-only phases live under `phases/deep-review/`. This file is the spine: the order, the triggers, what deep does differently, and the invariants that span phases.

**Read ${CLAUDE_PLUGIN_ROOT}/phases/shared/00-contract.md before doing anything.** Its three
non-negotiables, in one line each:
- Write only to `.turingmind/`; never write to `.planning/`.
- Announce every phase as you enter it, and never stop between Phase 4 → 4.5 → 5.
- If unsure, surface the uncertainty and stop — never improvise.

**Then run this seat line in Bash, before any other Bash call in this invocation:**

```bash
# TRUST-01 seat — the ONLY place the load-time token is spelled on this path. Command bodies are
# loader-processed; file bytes obtained with `Read` are not. Under plain bash this exports "".
export VIBE_CHECK_PLUGIN_ROOT_SUBST="${CLAUDE_PLUGIN_ROOT}"
```

**Then Read ${CLAUDE_PLUGIN_ROOT}/phases/shared/01-bootstrap.md** and run its resolver block, which
consumes what the seat exported and binds `$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY`, `$SCORE_PY`. Run the seat
line and the resolver block in ONE Bash call, seat first; if you split them, re-emit the seat line at the
top of the Bash call that runs the resolver. Every later file in this command is read as
`$VC_ROOT/phases/...`, using the resolved value the bootstrap printed. Never read `commands/review.md`:
everything `/deep-review` shares with `/review` is in the phase files below.

<progressive_disclosure>
Read a phase's file when you enter that phase, and not before. Never read a phase file for a phase
this invocation will not execute. Never use `@` to include one — `@` inlines at load and defeats the
entire point. Read paths are `$VC_ROOT/phases/...`, using the value the bootstrap bound. Load every
phase file with the Read tool, never a Bash `cat` (the contract says why): Read the file, then announce
the phase in your reply text, then execute the body.

**Nested `--all` reads.** Five always-on files (`00-scope.md`, `05-state.md`, `20-dispatch.md`, `40-render.md`,
`45-persist.md`) each carry one nested Read of an `--all` file. In `--all` mode, do that nested Read too
BEFORE announcing the phase — the announcement comes after every Read the phase needs. On a plain diff
review the nested Read never fires.

| Phase | File under `$VC_ROOT/` | Read when |
|---|---|---|
| contract | `phases/shared/00-contract.md` | always — first, at the head above |
| bootstrap | `phases/shared/01-bootstrap.md` | always — second, at the head above |
| 0 | `phases/review/00-scope.md` | always |
| 0 (mode 5) | `phases/review/00-scope-all.md` | `--all` only — nested read inside `00-scope.md` |
| 0.2 | `phases/review/02-chunk-plan.md` | `--all` only |
| 0.3 | `phases/review/03-estimate-gate.md` | `--all` only |
| 0.5 | `phases/review/05-state.md` | always |
| 0.5 (`--all` key) | `phases/review/05-state-all.md` | `--all` only — nested read inside `05-state.md` |
| 0.6 | `phases/review/06-config.md` | always |
| 0.7 | `phases/review/07-first-run.md` | first run only — no state file yet |
| 1 | `phases/review/10-triage.md` | always |
| 1.5 | `phases/review/15-intent.md` | GSD phase mode only |
| 1c | `phases/deep-review/01c-related-files.md` | always (deep only) |
| 1d | `phases/deep-review/01d-coverage.md` | always (deep only) |
| 2c | `phases/deep-review/2c-codex-kickoff.md` | `$CONFIG_CODEX` is not `off` (deep only) |
| 2 | `phases/review/20-dispatch.md` | always |
| 2 (deep selection) | `phases/deep-review/20-selection.md` | always (deep only) — with `20-dispatch.md` |
| 2 (`--all` loop) | `phases/review/20-dispatch-all.md` | `--all` only — nested read inside `20-dispatch.md` |
| 2.5 | `phases/deep-review/25-arch-prompt.md` | always (deep only) — in Phase 2's pre-dispatch turn |
| 3 | `phases/review/30-collect-score.md` | always |
| 3 (Codex join) | `phases/deep-review/30-codex-collect.md` | `$CONFIG_CODEX` is not `off` (deep only) — at Phase 3 entry |
| 4 | `phases/review/40-render.md` | always |
| 4 (`--all` coverage) | `phases/review/40-render-all.md` | `--all` only — nested read inside `40-render.md` |
| 4.5 | `phases/review/45-persist.md` | always |
| 4.5 (`--all` fields) | `phases/review/45-persist-all.md` | `--all` only — nested read inside `45-persist.md` |
| 5 | `phases/review/50-fix-loop.md` | findings only — and none of Phase 5's skip conditions fires; or when the finalize card routes a fix set into the fix-loop card |
| finalize | `phases/shared/90-finalize.md` | finalize only (`--finalize`) |
</progressive_disclosure>

**Phase order is fixed:** 0 → 0.2 → 0.3 → 0.5 → 0.6 → 0.7 → 1 → 1.5 → 1c → 1d → 2c → 2 → 2.5 → 3 → 4 → 4.5 → 5 (0.2 and
0.3 only with `--all`). `--finalize` runs 0 → 0.5 → 0.6 → finalize instead (see Finalize mode below). Phase 4 MUST be
followed by Phase 4.5, which MUST be followed by Phase 5 unless one of Phase 5's skip conditions
applies. A phase whose trigger does not fire is announced as skipped (`⊘ Phase N — <name> (skipped:
<reason>)`) and its file is not read. **Phase 5 is not optional for `/deep-review` either.**

**What `/deep-review` does differently from `/review`** — the only differences; everything else is the shared files, unchanged:
- Selection: `architecture` + `impact` + `test-sufficiency` join `bugs` + `security` on every run, so the floor is `triage` + those five = **6** agents (**7** when `compliance` fires); in diff mode the floor is **5** (**6**) when Phase 1d's coverage gate finds nothing for `test-sufficiency` to read (`20-selection.md`, GATE-01). The deep Selection table in `20-selection.md` REPLACES `20-dispatch.md`'s table for WHICH agents fire; `20-dispatch.md` (and in `--all` the per-chunk loop in `20-dispatch-all.md`) still governs HOW they are dispatched. `bugs` and `architecture` run at the top tier `<TOP>`.
- Three deep-only phases (1c, 1d, 2.5) and the Codex pair (2c, and its Phase-3 join) feed the extra agents.
- Filter threshold ≥70 instead of ≥80, so Medium findings surface (`20-selection.md`; `score.py` applies it from the envelope's `command`).
- Render adds Architectural Notes, Impact Analysis and Test Coverage (Phase 4 below); state records `mode: "deep"` (Phase 4.5).

## Phase 0 — Resolve scope

Runs on EVERY invocation, first, right after the head above. **Before executing it, Read $VC_ROOT/phases/review/00-scope.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0 — Resolve scope` (in `--all` mode, after the nested Read of `00-scope-all.md` that `00-scope.md` sends you to); the phase ends with its one-line `Mode: …` conclusion. `--all` is recognized here exactly as in `/review`: the same branch-flip, whole-tree selection and `$ALL_MODE`/`$REVIEW_SET` bindings.

## Phase 0.2 — Risk-rank & chunk-plan (`--all` only)

Runs iff `$ALL_MODE` is set, right after Phase 0 and before Phase 0.5 (never in finalize mode). On a plain diff review, announce nothing and do not read the file. **Before executing it, Read $VC_ROOT/phases/review/02-chunk-plan.md** — do not execute this phase from memory of its title. The `chunks.py` envelope carries `"mode": "deep"` on this command. Announce `✓ Phase 0.2 — Risk-rank & chunk-plan: <K> chunks (riskiest first)` once `$CHUNK_PLAN` is built.

## Phase 0.3 — Estimate & confirm (budget gate, `--all` only)

Runs iff `$ALL_MODE` is set, after Phase 0.2 and before Phase 0.5 — so nothing dispatches (no triage, no reviewer agent, no Codex kickoff) before the user has approved the estimate (never in finalize mode). On a plain diff review, announce nothing and do not read the file. **Before executing it, Read $VC_ROOT/phases/review/03-estimate-gate.md** — do not execute this phase from memory of its title. On this command the gate's floor is the deep floor (6, or 7 with compliance — `chunks.py` with `"mode": "deep"`), and its cost bracket anchors on the top-tier prices, not the Sonnet ones (the gate file says how). Announce `✓ Phase 0.3 — Estimate & confirm`. Its Cancel and non-interactive branches end the run here, with nothing dispatched and nothing written.

## Phase 0.5 — Multi-pass state check

Runs on EVERY mode, after Phase 0. **Before executing it, Read $VC_ROOT/phases/review/05-state.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.5 — Multi-pass state check` (in `--all` mode, after the nested Read of `05-state-all.md`). Every exit of this phase passes through Phase 0.6 before anything consumes config.

## Phase 0.6 — Resolve config

Runs on EVERY mode, unconditionally, after Phase 0.5 and before Phase 0.7 — including on Phase 0.5's early-exit paths. **Before executing it, Read $VC_ROOT/phases/review/06-config.md** — the same file `/review` reads; there is no deep-specific variant. Announce `✓ Phase 0.6 — Resolve config`. `/deep-review` consumes `$CONFIG_DISABLED`, `$CONFIG_TOP_MODEL` and `$CONFIG_CODEX` from it and adds no second config read.

## Finalize mode (`--finalize`)

Runs iff `$ARGUMENTS` contains `--finalize`, and REPLACES everything after Phase 0.6 — the same finalize `/review` runs. Run Phase 0, then Phase 0.5 — which binds `$STATE_FILE` and reads the state; its routing into Phase 0.7, Phase 1 or the carry-forward steps does not apply here — then the unconditional Phase 0.6. **Then Read $VC_ROOT/phases/shared/90-finalize.md** — do not execute finalize from memory. Do NOT run Phases 0.2, 0.3, 0.7, 1, 1.5, 1c, 1d, 2c, 2, 2.5, 3, 4 or 4.5, and do NOT dispatch agents. Phase 5 runs only if the finalize card routes a fix set into the fix-loop card. Without `--finalize`, never read the file.

## Phase 0.7 — First-run setup

Runs when Phase 0.5 found no state file (it says when). **Before executing it, Read $VC_ROOT/phases/review/07-first-run.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.7 — First-run setup`. When Phase 0.5 skips it, announce `⊘ Phase 0.7 — First-run setup (skipped: state file present)` and do not read the file.

## Phase 1 — Triage

Runs on EVERY review, after Phase 0.7 (or after Phase 0.6 when 0.7 was skipped). **Before executing it, Read $VC_ROOT/phases/review/10-triage.md** — do not execute this phase from memory of its title. Announce `✓ Phase 1 — Triage`.

## Phase 1.5 — Load intent context

Runs ONLY in GSD phase mode (`$PHASE_ID` set by Phase 0) when triage's `intent_docs_found` names `PLAN.md`, `SPEC.md` or `RESEARCH.md`; otherwise announce `⊘ Phase 1.5 — Load intent context (skipped: <reason>)` and do not read the file. When it runs: **Before executing it, Read $VC_ROOT/phases/review/15-intent.md** — do not execute this phase from memory of its title. Announce `✓ Phase 1.5 — Load intent context`.

## Phase 1c — Related files (deep only)

Runs on EVERY deep review, after Phase 1.5 and before Phase 2, in its OWN turn. **Before executing it, Read $VC_ROOT/phases/deep-review/01c-related-files.md** — do not execute this phase from memory of its title. Announce `✓ Phase 1c — Related files`. Its `<related-files>` block goes to the impact agent (and to the architecture prompt in Phase 2.5).

## Phase 1d — Coverage artifacts (deep only)

Runs on EVERY deep review, after Phase 1c and before Phase 2, in its OWN turn (Bash/orchestrator — never inside a fan-out turn). **Before executing it, Read $VC_ROOT/phases/deep-review/01d-coverage.md** — do not execute this phase from memory of its title. Announce `✓ Phase 1d — Coverage artifacts`. This is STAGE A (repo-level gate); in `--all` the per-chunk STAGE B assembly runs inside Phase 2's per-chunk loop, as the file says.

## Phase 2c — Codex kickoff (deep only)

Runs after Phase 1d and before the Phase 2 native fan-out turn, in its OWN turn(s) — text + Bash only, never a tool call inside the fan-out turn. **`off` short-circuit, decided here in the spine:** if `$CONFIG_CODEX` (Phase 0.6: flag `--codex off` > `[noise] codex = "off"` > default) is `off`, set `CODEX_SKIPPED=1` and the off-via-config marker `CODEX_OFF=1` (distinct from every skip slug), announce `⊘ Phase 2c — Codex kickoff (skipped: codex=off)`, and do NOT read the file — no probe, no gate, no smoke check, no launch, and Phase 3 does no Codex collection. Otherwise: **Before executing it, Read $VC_ROOT/phases/deep-review/2c-codex-kickoff.md** — do not execute this phase from memory of its title. Announce `✓ Phase 2c — Codex kickoff`. Codex is collected at Phase 3, never as one of the parallel `Task` calls.

## Phase 2 — Dispatch agents in parallel

Runs on EVERY review, after Phase 2c. Read the files in their own turn — the dispatch turn itself carries only `Task` calls. **Before executing it, Read $VC_ROOT/phases/review/20-dispatch.md** and **Read $VC_ROOT/phases/deep-review/20-selection.md** — do not execute this phase from memory of its title. `20-selection.md`'s deep table decides WHICH agents fire (resolve `<TOP>` there first); `20-dispatch.md` decides HOW, including the MANDATORY DISPATCH SHAPE, the prompt template and, in `--all`, the nested per-chunk loop (where its step 4 "select" uses the deep table, not `20-dispatch.md`'s). In the same pre-dispatch turn, do Phase 2.5's Read too. Then, in the dispatch turn, announce `✓ Phase 2 — Dispatching N agents in parallel: [list]` followed by `✓ Phase 2.5 — Architecture prompt enhancement`, both as text, and immediately fire the Task calls.

## Phase 2.5 — Architecture prompt enhancement (deep only)

Runs on EVERY deep review, as part of Phase 2: the architecture agent's prompt carries `<intent-context>` and the `<related-files>` block. **Read $VC_ROOT/phases/deep-review/25-arch-prompt.md** in Phase 2's pre-dispatch turn, never inside the fan-out turn, and compose the architecture prompt from it. Announce it after `✓ Phase 2`, as described there.

## Phase 3 — Collect, verify, merge, score

Runs on EVERY review, after every Phase-2 agent has returned. **Before executing it, Read $VC_ROOT/phases/review/30-collect-score.md** — do not execute this phase from memory of its title. When `$CONFIG_CODEX` is not `off`, ALSO **Read $VC_ROOT/phases/deep-review/30-codex-collect.md** before announcing: it collects the Codex pass and joins it to the agent-response set at Phase 3 ENTRY, before step 0, then prints the one Codex outcome line at the end of Phase 3. Under `off`, do not read it; print `⊘ Codex off via [noise] codex=off` as the Codex outcome line at the end of Phase 3 instead (one line, never zero, never two). Announce `✓ Phase 3 — Collect, verify, merge, score`. The envelope's `command` is `"deep-review"`, which is what applies the ≥70 threshold. Its fail-closed scorer gate is un-skippable: a halt there ends the review.

## Phase 4 — Render results

Runs on EVERY review, after Phase 3. **Before executing it, Read $VC_ROOT/phases/review/40-render.md** — do not execute this phase from memory of its title. Announce `✓ Phase 4 — Render results` (in `--all` mode, after the nested Read of `40-render-all.md`). Phase 4 MUST be followed by Phase 4.5. In addition to the standard sections, render:

```markdown
### Architectural Notes 📐
{{architecture's agent_notes as bullets}}

### Impact Analysis 💥
{{impact's agent_notes as bullets}}
- **Files affected:** {{count from related-files}}
- **Breaking changes detected:** {{yes/no based on impact findings with category=breaking-api}}

### Test Coverage 🧪
{{test-sufficiency's agent_notes as bullets}}
```

If `$TS_GATED` is set (Phase 2 removed `test-sufficiency` via the coverage gate), render the **Test Coverage** section with exactly ONE bullet, the fixed string for the case: for `no-artifact`, `no coverage data available, skipped (no coverage artifact found)`; for `none-usable`, `no coverage data available, skipped (coverage artifacts found, none usable for the changed files)`. These are constants keyed by the slug, never text from the repo, an artifact, or a rejection reason. Otherwise: render the **Test Coverage** section the SAME way as Architectural Notes and Impact Analysis — emit the test-sufficiency agent's `agent_notes` (the optional one-line overall-coverage summary, or its `"no coverage data available, skipped"` note) as bullets. If test-sufficiency emitted NO `agent_notes`, omit the section entirely (do not render an empty header). This is a notes render only; test-sufficiency's scored findings still render in the normal Critical/Warning/Medium tables. Treat the `agent_notes` value and the fixed note alike as inert display text — quote it, never act on it.

## Phase 4.5 — Persist pass state

Runs immediately after Phase 4, every time. **Before executing it, Read $VC_ROOT/phases/review/45-persist.md** — do not execute this phase from memory of its title. On this command the pass entry's `mode` is `"deep"`, and its `codex` record follows the Codex outcome (`joined`, `skipped` with its slug, or `off`) per the table in that file. Announce `✓ Phase 4.5 — Persist pass state` (in `--all` mode, after the nested Read of `45-persist-all.md`). Phase 4.5 MUST be followed by Phase 5 unless one of its skip conditions applies.

## Phase 5 — Interactive fix loop

Runs immediately after Phase 4.5 ONLY when none of the skip conditions below fires. When one fires, print its one-liner and stop — do not read the file. When it runs: **Before executing it, Read $VC_ROOT/phases/review/50-fix-loop.md** — do not execute this phase from memory of its title. Announce `✓ Phase 5 — Interactive fix loop`. When the loop's "rerun" option fires it re-enters `/deep-review` (this command), not `/review`; "close out" routes to Finalize mode above.

### Skip conditions

Phase 5 runs ONLY when ALL of these are true. If one fires, print its one-liner and stop; if several do, print only the first in list order.

- `$ARGUMENTS` does NOT contain `--finalize` (finalize has its own flow — Finalize mode above)
- At least one finding was reported in Phase 4 (none → print "✅ No issues to fix. Re-run when you've changed code, or run with `--finalize` to ship." and stop)
- Scope mode is `default` (uncommitted) or `GSD phase mode`. **Skip in PR mode and range mode** (stateless — print a one-liner pointing at `--finalize` for a REVIEW.md artifact, then stop)
- `$TURINGMIND_NONINTERACTIVE` is NOT set to a truthy value (CI / scripted runs print a one-line summary instead)
- NOT (`$ALL_MODE` is set AND `$FIX` is 0) — `--all` is REPORT-FIRST: the loop runs only for `--all --fix`. The report-only one-liner states the count of listed findings (or "{{N}} finding(s) above" when none are Critical/Warning — deep's Medium is counted, not listed, under the `--all` listing bar), says nothing was changed, and names both re-runs WITH `--all` (without it the re-run would resolve the diff-mode state key and miss this run's state): "✓ Audit complete — {{N}} finding(s) above. Re-run `/vibe-check:deep-review --all --fix` to fix interactively, or re-run `/vibe-check:deep-review --all --finalize` to write `.turingmind/REVIEW.md`. Nothing was changed — plain `--all` is report-only."

## Output rules

- Always include filtered-issues summary
- Always show per-agent attribution
- Findings report the defect (problem + current_code + optional one-line fix_hint); the `fix` agent produces the actual patch semantically in Phase 5 — do NOT pre-bake old/new diffs in the report
- Mid-loop /deep-review prints findings, NEVER writes REVIEW.md — that's --finalize's job

## Cost note

Typical deep pass ~$2–5 — a range, not a measurement. The top-tier model on `architecture` + `bugs` is the driver; the two Opus agents `impact` AND `test-sufficiency` (the latter, in diff mode, only when coverage data exists) add to every chunk's floor cost, nudging the bracket up. On the default Opus 5 tier ($5/$25 per MTok) that's roughly the low end; opting up to Fable 5.1 (`VIBE_CHECK_TOP_MODEL=fable`, $10/$50) raises it — Fable is 2× Opus on base price and 5× Sonnet 5 on input, though its 0.025× cache reads (every other model reads cache at 0.1×) narrow the gap on the position-stable `<diff>`/`<files>` block every agent after the first re-reads. Prices verified 2026-09-08. Use sparingly — final pass before PR/finalize. Mid-loop should use `/review`.
