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
| 2 | `phases/review/20-dispatch.md` | always |
| 2 (`--all` loop) | `phases/review/20-dispatch-all.md` | `--all` only — nested read inside `20-dispatch.md` |
| 3 | `phases/review/30-collect-score.md` | always |
| 4 | `phases/review/40-render.md` | always |
| 4 (`--all` coverage) | `phases/review/40-render-all.md` | `--all` only — nested read inside `40-render.md` |
| 4.5 | `phases/review/45-persist.md` | always |
| 4.5 (`--all` fields) | `phases/review/45-persist-all.md` | `--all` only — nested read inside `45-persist.md` |
| 5 | `phases/review/50-fix-loop.md` | findings only — and none of Phase 5's skip conditions fires; or when the finalize card routes a fix set into the fix-loop card |
| finalize | `phases/shared/90-finalize.md` | finalize only (`--finalize`) |
</progressive_disclosure>

**Phase order is fixed:** 0 → 0.2 → 0.3 → 0.5 → 0.6 → 0.7 → 1 → 1.5 → 2 → 3 → 4 → 4.5 → 5 (0.2 and
0.3 only with `--all`). `--finalize` runs 0 → 0.5 → 0.6 → finalize instead (see Finalize mode below). Phase 4 MUST be
followed by Phase 4.5, which MUST be followed by Phase 5 unless one of Phase 5's skip conditions
applies. A phase whose trigger does not fire is announced as skipped (`⊘ Phase N — <name> (skipped:
<reason>)`) and its file is not read.

## Phase 0 — Resolve scope

Runs on EVERY invocation, first, right after the head above. **Before executing it, Read $VC_ROOT/phases/review/00-scope.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0 — Resolve scope` (in `--all` mode, after the nested Read of `00-scope-all.md` that `00-scope.md` sends you to); the phase ends with its one-line `Mode: …` conclusion.

## Phase 0.2 — Risk-rank & chunk-plan (`--all` only)

Runs iff `$ALL_MODE` is set, right after Phase 0 (never in finalize mode). On a plain diff review, announce nothing and do not read the file. **Before executing it, Read $VC_ROOT/phases/review/02-chunk-plan.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.2 — Risk-rank & chunk-plan: <K> chunks (riskiest first)` once `$CHUNK_PLAN` is built.

## Phase 0.3 — Estimate & confirm (budget gate, `--all` only)

Runs iff `$ALL_MODE` is set, after Phase 0.2 and before Phase 0.5 — so before any state write, triage or dispatch (never in finalize mode). On a plain diff review, announce nothing and do not read the file. **Before executing it, Read $VC_ROOT/phases/review/03-estimate-gate.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.3 — Estimate & confirm`. Its Cancel and non-interactive branches end the run here, with nothing dispatched and nothing written.

## Phase 0.5 — Multi-pass state check

Runs on EVERY mode, after Phase 0. **Before executing it, Read $VC_ROOT/phases/review/05-state.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.5 — Multi-pass state check` (in `--all` mode, after the nested Read of `05-state-all.md`). Every exit of this phase passes through Phase 0.6 before anything consumes config.

## Phase 0.6 — Resolve config

Runs on EVERY mode, unconditionally, after Phase 0.5 and before Phase 0.7 — including on Phase 0.5's early-exit paths. **Before executing it, Read $VC_ROOT/phases/review/06-config.md** — do not execute this phase from memory of its title. Announce `✓ Phase 0.6 — Resolve config`.

## Finalize mode (`--finalize`)

Runs iff `$ARGUMENTS` contains `--finalize`, and REPLACES everything after Phase 0.6. Run Phase 0, then Phase 0.5 — which binds `$STATE_FILE` and reads the state; its routing into Phase 0.7, Phase 1 or the carry-forward steps does not apply here — then the unconditional Phase 0.6. **Then Read $VC_ROOT/phases/shared/90-finalize.md** — do not execute finalize from memory. Do NOT run Phases 0.2, 0.3, 0.7, 1, 1.5, 2, 3, 4 or 4.5, and do NOT dispatch agents. Phase 5 runs only if the finalize card routes a fix set into the fix-loop card. Without `--finalize`, never read the file.

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

Runs on EVERY review, after Phase 3. **Before executing it, Read $VC_ROOT/phases/review/40-render.md** — do not execute this phase from memory of its title. Announce `✓ Phase 4 — Render results` (in `--all` mode, after the nested Read of `40-render-all.md`). Phase 4 MUST be followed by Phase 4.5.

## Phase 4.5 — Persist pass state

Runs immediately after Phase 4, every time. **Before executing it, Read $VC_ROOT/phases/review/45-persist.md** — do not execute this phase from memory of its title. Announce `✓ Phase 4.5 — Persist pass state` (in `--all` mode, after the nested Read of `45-persist-all.md`). Phase 4.5 MUST be followed by Phase 5 unless one of its skip conditions applies.

## Phase 5 — Interactive fix loop

Runs immediately after Phase 4.5 ONLY when none of the skip conditions below fires. When one fires, print its one-liner and stop — do not read the file. When it runs: **Before executing it, Read $VC_ROOT/phases/review/50-fix-loop.md** — do not execute this phase from memory of its title. Announce `✓ Phase 5 — Interactive fix loop`.

### Skip conditions

Phase 5 runs ONLY when ALL of these are true:

- `$ARGUMENTS` does NOT contain `--finalize` (finalize has its own dedicated flow — Finalize mode above)
- At least one finding was reported in Phase 4 (no findings → nothing to fix; print "✅ No issues to fix. Re-run when you've changed code, or run with `--finalize` to ship." and stop)
- Scope mode is `default` (uncommitted) or `GSD phase mode` — stateful modes where rerun-with-carry-forward makes sense. **Skip Phase 5 entirely in PR mode and range mode** (both are stateless — print a one-liner pointing the user at `--finalize` if they want a REVIEW.md artifact, then stop)
- The `$TURINGMIND_NONINTERACTIVE` env var is NOT set to a truthy value (CI / scripted runs disable the loop; print a one-line summary instead)
- NOT (`$ALL_MODE` is set AND `$FIX` is 0) — in `--all` mode the fix loop is REPORT-FIRST: it runs only when `--all --fix` was passed. A plain `--all` run (no `--fix`) renders + persists (Phases 4 / 4.5) then skips Phase 5 and prints the report-only one-liner below. `$ALL_MODE`-guarded — diff mode (Phase 0 modes 1-4) never sets `$ALL_MODE`, so this clause is always-true (non-skipping) there, leaving the diff-mode fix loop byte-stable. This is an EXTENSION of the existing skip-and-note posture, NOT a new flag or mechanism. (FIX-01 / FIX-02)

If any skip condition fires, print the contextual one-liner and stop normally. If MORE THAN ONE skip condition applies to a run, print ONLY the first applicable condition's one-liner in list order (top-to-bottom) and stop — never two messages.

When the report-first clause above is the first applicable skip condition (a plain `--all` run that reached Phase 5 — i.e. at least one finding was reported in Phase 4, no earlier bullet having fired), its contextual one-liner is the report-only line: state the count of LISTED findings (Critical + Warning — the bands the report shows under the listing bar), then name BOTH follow-up paths — re-run this command with `--all --fix` to fix interactively, and re-run with `--all --finalize` to write `.turingmind/REVIEW.md` — plus a "report-only — nothing was changed" note so the stop never reads as a bug or dead end. BOTH follow-up hints MUST carry the `--all` token: `--all` is what sets `$ALL_MODE` (Phase 0 branch-flip), and `$ALL_MODE` is what makes Phase 0.5 resolve this run's `$ALL_STATE_FILE` (the reserved `by-mode/all/<scope-hash>.json` key). A BARE `--finalize` (or bare `--fix`) re-run would NOT set `$ALL_MODE`, so it would resolve the DEFAULT diff-mode state key and miss this `--all` run's persisted state entirely (erroring "No prior review passes", or worse, finalizing an unrelated stale diff-mode pass) — so `--all` is mandatory on the advertised re-runs, matching the design spec's "all flags compose" invocation model (§7). Render this command's own `--all` form for BOTH hints (the SINGLE command currently running, by positional self-identity — the same "this command" signal Phase 3 uses for the envelope's `command`): show `/vibe-check:review --all --fix` and `/vibe-check:review --all --finalize` when running `/review`, and `/vibe-check:deep-review --all --fix` and `/vibe-check:deep-review --all --finalize` when running `/deep-review` — each rendered hint names ONE command (its own), never a static list of both, and never a `$COMMAND`/mustache-style command variable. If the run produced findings but NONE fall in the listed Critical/Warning bands (the `/deep-review --all` Medium-only case — Medium is counted-not-listed under the listing bar), phrase the count generically ("{{N}} finding(s) above") rather than asserting a Critical/Warning count of 0, so the line reads sensibly when no C/W findings exist. For example, when `/review` is running: "✓ Audit complete — {{N}} finding(s) above. Re-run `/vibe-check:review --all --fix` to fix interactively, or re-run `/vibe-check:review --all --finalize` to write `.turingmind/REVIEW.md`. Nothing was changed — plain `--all` is report-only." (under `/deep-review`, the hints read `/vibe-check:deep-review --all --fix` and `/vibe-check:deep-review --all --finalize` instead.)

## Output rules

- Always include filtered-issues summary
- Always show per-agent attribution
- Findings report the defect (problem + current_code + optional one-line fix_hint); the `fix` agent produces the actual patch semantically in Phase 5 — do NOT pre-bake old/new diffs in the report
- In-diff findings are trusted more, not exclusively reported (Fable A12 honesty fix): the orchestrator recomputes `in_diff` from the raw hunks (overriding agent claims) and score.py grants it +20 — but an out-of-diff finding is NOT auto-dropped; without the +20 most fall sub-threshold, and a rare high-confidence pre-existing defect CAN surface (deliberate: a sole-reviewer tool suppressing a conf-95 finding because it predates the diff would be silent false-negative territory)
- Mid-loop /review prints findings, NEVER writes REVIEW.md — that's --finalize's job
- Phase 5 fix-loop runs after every non-finalize, non-stateless invocation that has at least one finding
