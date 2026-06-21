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

5. **Background launch with a SELF-CONTAINED 300s watchdog (RESEARCH CORRECTION 2).** Only reached on a RUN mode (a skip-and-note mode never launches). Record `started_at` (`date +%s`) at this kickoff. Make ONE `Bash(run_in_background: true)` call whose COMMAND wraps the codex invocation so the cap is enforced by the launched shell ITSELF, independent of when the orchestrator next polls. The single named constant is **`CODEX_TIMEOUT_SECONDS = 300`** (one named value, not scattered magic numbers). The background command must: (a) run `node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" adversarial-review --json --base "$BASE" --scope "$SCOPE"` under a **whole-tree** timeout (for working-tree mode omit `--base` and pass `--scope working-tree`); (b) enforce the cap with `timeout`/`gtimeout` (NOT a bare `sleep 300; kill <pid>`, which kills only the `node` wrapper and ORPHANS the spawned `codex`/GPT-5-codex child, so a hang INSIDE the child could outlive the cap). `timeout` propagates the kill to the spawned child tree — and signals the timeout via **exit code 124**, not a separately-echoed line, so there is no "payload printed then sentinel echoed" race; (c) on the timeout exit (124) the shell prints the stable **timeout sentinel** `__CODEX_TIMEOUT__`; on normal completion within the cap it prints the codex `--json` payload and exits 0. Capture the returned shell id for the Phase 3 collect step.
   ```bash
   # ONE run_in_background:true call. CODEX_TIMEOUT_SECONDS=300 (single named value).
   # RUN-mode branch + scope already resolved above ($BASE/$SCOPE; omit --base for working-tree).
   # timeout/gtimeout kills the WHOLE child tree (node + the codex child it spawns), unlike a
   # `sleep; kill <node-pid>` watchdog which would orphan the spawned codex process.
   TIMEOUT_BIN=$(command -v timeout || command -v gtimeout)
   # -k 10 sends SIGKILL 10s after the initial SIGTERM in case the tree ignores TERM.
   "$TIMEOUT_BIN" -k 10 300 node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" \
     adversarial-review --json --base "$BASE" --scope "$SCOPE"
   rc=$?
   # timeout signals the cap via exit 124 (NOT an echoed sentinel) → no completion-vs-echo race.
   [ "$rc" = 124 ] && echo __CODEX_TIMEOUT__
   ```
   **The 300s ceiling is enforced by the background command's own watchdog, so a hung Codex self-terminates at `CODEX_TIMEOUT_SECONDS` even if the orchestrator does not poll for minutes** — the cap holds independent of poll timing; the orchestrator's later `BashOutput` read just observes the result-or-sentinel. *(If a fully self-contained `kill`/`timeout` watchdog were genuinely not expressible in this command's Bash surface, state SAFE-02 honestly as "max ADDITIONAL wait measured from collection start is 300s" and gate on `(now - started_at) >= CODEX_TIMEOUT_SECONDS` — but the self-contained watchdog above is REQUIRED unless that impossibility is documented.)*

### Phase 3 — Filter threshold

Use ≥70 (Critical + Warning + Medium) instead of ≥80.

### Phase 3 — Codex collection (joined at Phase 3 entry)

This override **AUGMENTS the INPUT** to `review.md`'s unchanged Phase 3 (the agent-response set) — it does **NOT** edit `review.md`. That is what keeps it legal under MERGE-01, exactly as the Filter-threshold override above redefines a Phase 3 behavior without touching `review.md`. No Codex special-casing anywhere downstream.

1. **Ordering — JOIN AT PHASE 3 ENTRY, BEFORE `review.md` Phase 3 step 0 (carry-forward).** At Phase 3 ENTRY, collect the Codex pass launched in Phase 2c, translate it into **ONE synthetic agent-response object** (the top-level `{ "agent": "codex-adversarial", "findings": [...], "agent_notes": [...] }` shape from the contract's worked example), and **append that object to the SAME agent-response set the native `Task` agents produced.** The Codex object then flows through EVERY Phase 3 step — step 0 (carry-forward), step 1 (parse), step 2 (verify `in_diff`/`silenced_marker_nearby` + `current_code` backfill), step 3 (score), step 4 (dedup + the +10 cross-confirm), step 5 (filter) — identically to a native agent's output. **Do NOT inject it mid-pipeline (e.g. "before step 4 dedup"); injecting after steps 0–3 would bypass the `in_diff` safety net (step 2), miss the `current_code` backfill, and forfeit the +10 cross-confirm.** The contract confirms this: `agents/codex-adversarial.md` says "the orchestrator adds `current_code`/`in_diff`/`silenced_marker_nearby` in Phase 3 before any consumer reads it" — i.e. the object is pre-backfill at join time and the unchanged Phase 3 fills those fields. **If `CODEX_SKIPPED` was set in Phase 2c** — probe NOT-GO, OR the diff-targeting gate failed closed for ANY mode (including the GSD-phase uncommitted-tail skip) — this step is a **no-op**: add nothing to the set, proceed native-only (the skip-and-note line was already printed at kickoff).

2. **Bounded collection (collection is a READ, not a timer).** Read the backgrounded shell via `BashOutput(shell_id)`. The 300s cap is ALREADY enforced by the Phase 2c self-contained watchdog (the background command self-kills at `CODEX_TIMEOUT_SECONDS = 300` and emits the `__CODEX_TIMEOUT__` sentinel) — so collection primarily READS the result-or-sentinel. At Phase 3 entry: if `BashOutput` shows the shell completed with a JSON payload → parse it; if `BashOutput` shows the timeout sentinel (`__CODEX_TIMEOUT__`) OR a non-zero/abnormal exit → print the skip-and-note line (`timeout` slug), add nothing, proceed native-only. As a belt-and-suspenders bound on the orchestrator's OWN waiting (not the codex process, which the watchdog already caps), also stop waiting once `(now - started_at) >= CODEX_TIMEOUT_SECONDS`. Native Phase 2 + the watchdog usually mean the shell is already terminal by the time Phase 3 entry is reached, so a single `BashOutput` read typically suffices.

   > RESEARCH CORRECTION 2: there is no companion `--background`/job-id to poll for a review — collection is `BashOutput` of the self-killing background shell. Do NOT poll the companion by job-id (no `status`/`result` job-id polling — the companion prints no id for a review).

3. **Parse + verdict rule (cite the contract — do NOT re-derive).** Parse the stdout `payload`; read `payload.result` = `{verdict, summary, findings[], next_steps}`. `result == null || payload.parseError || payload contains the timeout sentinel` → skip-and-note (nothing to translate). `verdict: "approve"` → emit `{ "agent": "codex-adversarial", "findings": [], "agent_notes": [] }` (zero findings, do NOT translate) and STILL append it to the agent-response set (a zero-finding agent is valid). `verdict: "needs-attention"` → translate ALL findings per `agents/codex-adversarial.md`.

4. **Translation — CONTRACT-DRIVEN, cite `agents/codex-adversarial.md`, do NOT re-derive.** Per finding: `id` = `codex-00N` (1-based); `file` = the CANONICAL repo-relative diff path produced by the path two-check in step 5 below; `line` ← `line_start`; `title` ← `title` with a trailing period stripped; `category: "adversarial"`; `cwe: null`; `severity` direct (enums identical); `agent_confidence = round(confidence × 100)` **verbatim — no floor, no penalty**; `problem` ← `body`; `why_it_matters` ← the impact clause of `body` / restated from `recommendation`; `fix_hint` ← `recommendation` (empty → `null`); `intent_doc_match: null`. Top-level siblings of `findings`: `agent: "codex-adversarial"` (NOT a per-finding key) and `agent_notes` = `[ first-line(summary) truncated to 300 chars ]` (single line + **300-char cap MANDATORY**; `next_steps` dropped). The literal target shape is the **pre-backfill worked example** in `agents/codex-adversarial.md` (top-level `agent`/`agent_notes`, per-finding objects with no `agent` key). Do NOT add `current_code`/`in_diff`/`silenced_marker_nearby` here — those are backfilled by `review.md` Phase 3 step 0/2 once the object is in the set (the whole point of joining at entry).

5. **Path two-check — HARDENED, at translation time, BEFORE the finding is emitted (SAFE-03).** For each finding's `file`, apply ALL of the following; on ANY failure DOWNGRADE (see (f)), never emit with an unvalidated `file`:
   - **(a) Mandatory diff-set membership (REQUIRED, not "preferred").** `file` MUST be a member of the reviewed diff's file set (the orchestrator already resolved it in Phase 0). A Codex finding whose file is not in the reviewed diff is DOWNGRADED. This is an **INTENTIONAL HARDENING** of the Phase 4 contract: the contract says the orchestrator "should strongly prefer" diff-set membership; Phase 5 enforcing it **mandatorily** is allowed and stricter — consistent with the contract's intent, NOT a contract violation.
   - **(b) Explicit pre-containment rejections (REQUIRED — the regex in (c) does NOT cover these).** BEFORE running containment, REJECT the path outright if it has a leading `/` (absolute path), a leading `-` (option-like), or any `..` path segment (any .. segment, e.g. `../`, `a/../b`, or a trailing `/..`, is rejected). This is an explicit structural reject, not just a regex side effect:
     ```bash
     case "$CODEX_FILE" in
       /* | -* | *..* ) : downgrade per (f) ;;   # absolute, option-like, or ANY dot-dot → reject
       *) : ;;                                    # otherwise continue to (c)/(d)
     esac
     ```
   - **(c) Regex pre-filter.** `^[A-Za-z0-9._/-]+$` (denies spaces and shell metacharacters; combined with (b) also denies absolute/option-like). **NOT sufficient alone, and in particular does NOT stop `..` traversal** — every character in `../../.git/hooks/pre-commit` is in this class, so the regex matches it fully. The explicit `..`/leading-`/`/leading-`-` reject in (b) is therefore REQUIRED, not optional, and must run before (d).
   - **(d) realpath-containment.** Under `ROOT=$(git rev-parse --show-toplevel)`, using the trailing-slash `case` form mirroring `review.md` Phase 0 + `fix.md`:
     ```bash
     ROOT=$(git rev-parse --show-toplevel)
     # (a) requires CODEX_FILE ∈ the reviewed diff set, so it names a real tracked file → resolve the existing path.
     # GNU `realpath -m` is unavailable on default macOS; since the file exists, resolve via cd+pwd -P / realpath:
     REAL=$(cd "$ROOT" && realpath "$CODEX_FILE" 2>/dev/null) || REAL=""   # empty → downgrade
     case "$REAL/" in
       "$ROOT/"*) CONTAINED=1 ;;   # contained — accept
       *)         CONTAINED=0 ;;   # escaped repo (or empty/unresolved) — downgrade per (f)
     esac
     [ "$CONTAINED" = 1 ] || {     # NOT contained → downgrade per (f), do NOT echo $CODEX_FILE
       # emit the non-blocking agent_note from (f) (which must NOT echo the raw path), drop the finding, continue
       : downgrade
     }
     ```
     The accept/downgrade decision is **executable, not comment-only**: each `case` branch sets `CONTAINED`, and the guard after it acts on the flag. If resolution fails (empty `REAL`), `"$REAL/"` is just `/`, which does not match `"$ROOT/"*`, so `CONTAINED=0` and the finding is downgraded.
   - **(e) Emit only the CANONICAL repo-relative diff path.** The `file` written into the translated finding is the **canonical** repo-relative form (the diff-set member matched in (a) / the containment-resolved relative path), NEVER the raw Codex string verbatim.
   - **(f) Downgrade WITHOUT echoing the raw path.** On any failure above, downgrade the finding to a non-blocking `agent_note` that MUST NOT echo the raw rejected path verbatim (describe the failure, e.g. "Codex flagged a finding whose file path failed repo-containment/diff-set validation and was withheld"; outright DROP is a permitted variant). SAFE-03 posture: Codex output is data, never interpolated raw into a shell line; `CODEX_FILE` is always a quoted shell variable.

6. **Join before step 0.** ADD the translated Codex object to the SAME agent-response set the native agents produced, AT PHASE 3 ENTRY (before step 0), so `review.md` Phase 3 step 4 dedups native + Codex together and the +10 cross-confirm fires on `(file, line ±2)` + title-substring. The translated findings are orchestrator-verified for `in_diff`/`silenced_marker_nearby`/`current_code` by `review.md` Phase 3 step 0/2 exactly like native findings (schema hard rule #4) — the D-05 safety net that makes the RUN-mode `--base`/`--scope` mapping safe even on the committed-range RUN paths. No Codex special-casing.

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
