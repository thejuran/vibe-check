---
allowed-tools: Bash(git:*), Bash(gh pr diff:*), Bash(gh pr view:*), Read, Write, Edit, Grep, Glob, Task, AskUserQuestion
description: Quick code review for uncommitted local changes
---

This command is an **orchestrator**. It runs the review phases listed below, in order, and each phase's
full instructions live in their own file under the plugin's `phases/` directory, loaded only when that
phase runs. This file is the spine: the order, the triggers, and the invariants that span phases.

**Read ${CLAUDE_PLUGIN_ROOT}/phases/shared/00-contract.md before doing anything.** Its three
non-negotiables, in one line each:
- Write only to `.turingmind/`; never write to `.planning/`.
- Announce every phase as you enter it, and never stop between Phase 4 → 4.5 → 5.
- If unsure, surface the uncertainty and stop — never improvise.

**Then run this seat line in Bash, before any other Bash call in this invocation:**

```bash
# TRUST-01 seat — the plugin-root token on the line below is a LOAD-TIME TEXT SUBSTITUTION by Claude Code
# (the exact braced spelling only; the unbraced form and the bash-default form are NOT substituted, and the
# shell variable is UNSET). The assignment below is the ONLY place that token is spelled on the orchestrator
# path, because command bodies are loader-processed and file bytes obtained with `Read` are not. Under plain
# bash it exports "". (A4: this comment deliberately does NOT spell the token — the seat invariant at
# behavior line "Static (A1 — the SEAT invariant)" permits it only on the export line or in a Read path.)
export VIBE_CHECK_PLUGIN_ROOT_SUBST="${CLAUDE_PLUGIN_ROOT}"
```

**Then Read ${CLAUDE_PLUGIN_ROOT}/phases/shared/01-bootstrap.md** and run its resolver block, which
consumes what the seat exported and binds `$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY`, `$SCORE_PY`. Run the seat
line and the resolver block in ONE Bash call, seat first; if you split them, re-emit the seat line at the
top of the Bash call that runs the resolver. Every later file in this command is read as
`$VC_ROOT/phases/...`, using the resolved value the bootstrap printed.

**Reached through `/deep-review`?** Then you loaded this file with the Read tool, so the plugin-root
token in the three places above was NOT substituted — you will see it spelled literally. Do not run
the seat line above: `/deep-review`'s own seat line, which its command body substituted, is the seat
for this invocation — use it wherever this section says "the seat line". Read the two shared files
under the plugin root that seat line names, then continue exactly as below.

<progressive_disclosure>
Read a phase's file when you enter that phase, and not before. Never read a phase file for a phase
this invocation will not execute. Never use `@` to include one — `@` inlines at load and defeats the
entire point. Read paths are `$VC_ROOT/phases/...`, using the value the bootstrap bound. Load every
phase file with the Read tool, never a Bash `cat` (the contract says why): Read the file, then announce
the phase in your reply text, then execute the body.

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
| 2 | `phases/review/20-dispatch.md` | always |
| 2 (`--all` loop) | `phases/review/20-dispatch-all.md` | `--all` only — nested read inside `20-dispatch.md` |
| 3 | `phases/review/30-collect-score.md` | always |
| 4 | `phases/review/40-render.md` | always |
| 4 (`--all` coverage) | `phases/review/40-render-all.md` | `--all` only — nested read inside `40-render.md` |
| 4.5 | `phases/review/45-persist.md` | always |
| 4.5 (`--all` fields) | `phases/review/45-persist-all.md` | `--all` only — nested read inside `45-persist.md` |
| 5 | `phases/review/50-fix-loop.md` | findings only — and none of Phase 5's skip conditions fires |
| finalize | `phases/shared/90-finalize.md` | finalize only (`--finalize`) |
</progressive_disclosure>

**Phase order is fixed:** 0 → 0.5 → 0.6 → 0.7 → 1 → 1.5 → 2 → 3 → 4 → 4.5 → 5. Phase 4 MUST be
followed by Phase 4.5, which MUST be followed by Phase 5 unless one of Phase 5's skip conditions
applies. A phase whose trigger does not fire is announced as skipped (`⊘ Phase N — <name> (skipped:
<reason>)`) and its file is not read.

## Phase 0 — Resolve scope

Runs on EVERY invocation, first, right after the head above. **Before executing it, Read $VC_ROOT/phases/review/00-scope.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0 — Resolve scope`; the phase ends with its one-line `Mode: …` conclusion.

## Phase 0.5 — Multi-pass state check

Runs on EVERY mode, after Phase 0. **Before executing it, Read $VC_ROOT/phases/review/05-state.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.5 — Multi-pass state check`. Every exit of this phase passes through Phase 0.6 before anything consumes config.

## Phase 0.6 — Resolve config

Runs on EVERY mode, unconditionally, after Phase 0.5 and before Phase 0.7 — including on Phase 0.5's early-exit paths. **Before executing it, Read $VC_ROOT/phases/review/06-config.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.6 — Resolve config`.

## Phase 0.7 — First-run setup

Runs when Phase 0.5 found no state file (it says when). **Before executing it, Read $VC_ROOT/phases/review/07-first-run.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.7 — First-run setup`. When Phase 0.5 skips it, announce `⊘ Phase 0.7 — First-run setup (skipped: state file present)` and do not read the file.

## Phase 1 — Triage

Runs on EVERY review, after Phase 0.7 (or after Phase 0.6 when 0.7 was skipped). **Before executing it, Read $VC_ROOT/phases/review/10-triage.md** — do not execute this phase from memory of its title. Announce `✓ Phase 1 — Triage`.

## Phase 1.5 — Load intent context

Runs ONLY in GSD phase mode (`$PHASE_ID` set by Phase 0) when triage's `intent_docs_found` names `PLAN.md`, `SPEC.md` or `RESEARCH.md`; otherwise announce `⊘ Phase 1.5 — Load intent context (skipped: <reason>)` and do not read the file. When it runs: **Before executing it, Read $VC_ROOT/phases/review/15-intent.md** — do not execute this phase from memory of its title. Announce `✓ Phase 1.5 — Load intent context`.

## Phase 2 — Dispatch agents in parallel

Runs on EVERY review, after Phase 1 / 1.5. Read the file in its own turn — the dispatch turn itself carries only `Task` calls. **Before executing it, Read $VC_ROOT/phases/review/20-dispatch.md** — do not execute this phase from memory of its title. Announce `✓ Phase 2 — Dispatching N agents in parallel: [list]` once the selection is settled.

## Phase 3 — Collect, verify, merge, score

Runs on EVERY review, after every Phase-2 agent has returned. **Before executing it, Read $VC_ROOT/phases/review/30-collect-score.md** — do not execute this phase from memory of its title. Announce `✓ Phase 3 — Collect, verify, merge, score`. Its fail-closed scorer gate is un-skippable: a halt there ends the review.

## Phase 4 — Render results

Runs on EVERY review, after Phase 3. **Before executing it, Read $VC_ROOT/phases/review/40-render.md** — do not execute this phase from memory of its title. Announce `✓ Phase 4 — Render results`. Phase 4 MUST be followed by Phase 4.5.

## Phase 4.5 — Persist pass state

Runs immediately after Phase 4, every time. **Before executing it, Read $VC_ROOT/phases/review/45-persist.md** — do not execute this phase from memory of its title. Announce `✓ Phase 4.5 — Persist pass state`. Phase 4.5 MUST be followed by Phase 5 unless one of its skip conditions applies.

## Output rules

- Always include filtered-issues summary
- Always show per-agent attribution
- Findings report the defect (problem + current_code + optional one-line fix_hint); the `fix` agent produces the actual patch semantically in Phase 5 — do NOT pre-bake old/new diffs in the report
- In-diff findings are trusted more, not exclusively reported (Fable A12 honesty fix): the orchestrator recomputes `in_diff` from the raw hunks (overriding agent claims) and score.py grants it +20 — but an out-of-diff finding is NOT auto-dropped; without the +20 most fall sub-threshold, and a rare high-confidence pre-existing defect CAN surface (deliberate: a sole-reviewer tool suppressing a conf-95 finding because it predates the diff would be silent false-negative territory)
- Mid-loop /review prints findings, NEVER writes REVIEW.md — that's --finalize's job
- Phase 5 fix-loop runs after every non-finalize, non-stateless invocation that has at least one finding
