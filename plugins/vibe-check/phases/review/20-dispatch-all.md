# Phase 2 — `--all` per-chunk dispatch

> **Lazy-loaded.** Read from `phases/review/20-dispatch.md` (at the top of Phase 2) when `$ALL_MODE` is set. A plain diff review never reads it.
> Part of Phase 2 — Read this file before any Phase 2 announcement. Each chunk then announces its own dispatch line (loop step 4): `✓ Phase 2 (chunk i/<K>) — Dispatching N_i agents in parallel: [list]`.

**What stays in `20-dispatch.md`.** The MANDATORY DISPATCH SHAPE, the Selection table, the model tiering, the base prompt template, the substitution bindings, and the architecture/compliance intent variant all live there and apply here unchanged. This file carries only what `--all` overrides or adds. The `<files>` block format below is prose on purpose (its bytes must stay identical across a chunk's agents for the prompt cache) — do not move it into a script.

**`$ALL_MODE` override of "the next assistant turn … is Phase 3" (Codex round-1 Finding 1 — applies INSIDE the per-chunk loop, Site C):** in `--all` mode the dispatch shape above runs ONCE PER CHUNK (the per-chunk dispatch loop in "`--all` mode — per-chunk dispatch loop" below). For a chunk `i`, the assistant turn AFTER chunk `i`'s N_i agents return does **NOT** go to Phase 3 — it ACCUMULATES the N_i responses into the run-level `AGENT_RESPONSES` set and CONTINUES to chunk `i+1`. The "next assistant turn … is Phase 3" sentence in `20-dispatch.md` is the single-dispatch (diff-mode) shape; in `--all` it is SUPERSEDED per chunk by accumulate-and-continue. Phase 3 runs exactly ONCE, AFTER the loop exits, over the accumulated `AGENT_RESPONSES`. This override governs every chunk's post-fan-out turn.

**`--all` form of the two substitution bindings** (the diff-mode forms are in `20-dispatch.md`'s **Substitution bindings**; these are the single-unit `--all` forms, superseded per chunk by the override that follows):
- `{{git_diff_output}}` — **In `--all` mode (`$ALL_MODE` set): `$FILES_BLOCK`** (the `<files>` block string built below) instead of a diff.
- `{{filtered_file_list}}` — **In `--all` mode: `$REVIEW_SET`** (the regular-files-only selected set) rendered as a name list.

**Per-chunk binding override (`$ALL_MODE` set — Codex round-2 Finding A; supersedes the two single-unit `--all` bindings above INSIDE the per-chunk dispatch loop):** the per-chunk loop (Site C, below) runs once per chunk of `$CHUNK_PLAN`, so BOTH halves of every chunk's agent prompt MUST be scoped to the CURRENT chunk, not the whole set. INSIDE the loop, for chunk `i`:
- `{{git_diff_output}}` ← **`$FILES_BLOCK_i`** (chunk `i`'s `<files>` block, built per chunk from the skip-filtered `$CHUNK_REVIEW_FILES_i` per the build-once rule below) — NOT the whole-set `$FILES_BLOCK`.
- `{{filtered_file_list}}` / `<changed-files>` ← **`$CHUNK_REVIEW_FILES_i`** (chunk `i`'s skip-filtered file-name list — `$CHUNK_FILES_i` MINUS that chunk's triage `files_to_skip_i`, see the loop's filter step — rendered as a name list) — **NOT the raw `$CHUNK_FILES_i`, NOT `$REVIEW_SET`**.

So both the `<files>` content block AND the `<changed-files>` name list are chunk-scoped, skip-filtered, and CONSISTENT: every chunk's agents see exactly chunk `i`'s SURVIVING contents AND are told exactly those same files are in scope (`$FILES_BLOCK_i` is built from the SAME `$CHUNK_REVIEW_FILES_i` the name-list binds to, so the two halves never diverge). This override governs EVERY chunk's dispatch — the whole-set `$REVIEW_SET` name-list binding (the single-unit `--all` binding above) is NOT reachable inside the loop; it applies only to a (now-superseded) single-unit reference.

🚫 **ANTI-PATTERN (Codex round-2 Finding A):** In the per-chunk loop do NOT bind `{{filtered_file_list}}`/`<changed-files>` to the whole `$REVIEW_SET` — that tells every chunk's agents the whole repo is in scope while they only see chunk `i`'s contents, so they read/report outside the chunk and break the chunk budget/order guarantee. Both halves bind to chunk `i`'s skip-filtered list: content ← `$FILES_BLOCK_i` (built from `$CHUNK_REVIEW_FILES_i`), name-list ← `$CHUNK_REVIEW_FILES_i`.

### `--all` mode — `<files>` block swap (REVIEW-01, D-07/D-08)

When `$ALL_MODE` is set, swap the `<diff>` block for a `<files>` block in BOTH prompt templates (the base template AND the architecture/compliance intent variant, both in `20-dispatch.md`). The `<files>` block goes in the EXACT position the `<diff>` block occupied — for the base template that is right after the agent-name sentence; for the intent variant that is AFTER `{{intent_context_block_if_present}}`. The `<changed-files>` block and everything else are unchanged. So the base template in `--all` reads:

````
You are the {{agent_name}} agent. Review this code per your subagent instructions.

<files>
{{git_diff_output}}
</files>

<changed-files>
{{filtered_file_list}}
</changed-files>

The full file contents are provided above. Return ONE JSON object per templates/agent-output-schema.md. JSON only.
````

**`<files>` block format (`$FILES_BLOCK`).** A per-file fenced code block: a `### <path>` header line, then a fenced block whose fence language is a hint inferred from the file extension. Build it ONLY from `$REVIEW_SET` (the regular-files-only set from `00-scope-all.md`) — so dropped symlinks (git mode 120000) contribute NO contents (FINDING 3, end-to-end). Extension → fence-language hint mapping (Claude's discretion): `.py`→python, `.ts`/`.tsx`→typescript, `.js`/`.jsx`/`.mjs`/`.cjs`→javascript, `.go`→go, `.rs`→rust, `.md`→markdown, `.json`→json, `.yaml`/`.yml`→yaml, `.sh`→bash; unknown extension → bare fence (no language hint). Shape:

````
<files>
### path/to/file.py
```python
<full file contents>
```

### path/to/other.ts
```typescript
<full file contents>
```
</files>
````

**Build `$FILES_BLOCK` ONCE** in deterministic `git ls-files` lexicographic order (already stable) and substitute the IDENTICAL string into every agent prompt — keep per-agent variation OUTSIDE the block (agent-name sentence + intent-context only), exactly as the `<diff>` block does today (the position-stability rule in `20-dispatch.md`). The MANDATORY DISPATCH SHAPE is UNCHANGED — `--all` still fans out N Task calls in ONE assistant turn (do NOT split the dispatch into two turns).

### `--all` mode — per-chunk dispatch loop (CHUNK-03, D-05; the load-bearing seam)

**`--all` mode (`$ALL_MODE` set) — per-chunk dispatch (additive; the diff-mode dispatch + the MANDATORY DISPATCH SHAPE block in `20-dispatch.md` are byte-unchanged).** In `--all` mode the single whole-set dispatch is replaced by a **sequential per-chunk loop** over `$CHUNK_PLAN` (the risk-ranked chunk plan from Phase 0.2, chunk #1 = riskiest seed). Chunks are processed ONE AT A TIME in risk order (D-05: sequential ACROSS chunks; parallel agent fan-out WITHIN each chunk).

**Precondition (`$ALL_MODE` set) — `$CHUNK_PLAN` MUST exist and be non-empty before entering the per-chunk loop.** Because Phase 0.2 is numbered to run BEFORE this phase, `$CHUNK_PLAN` is normally already built. Defensive guard: if `$ALL_MODE` is set but `$CHUNK_PLAN` is unset or empty when you reach this loop, do NOT improvise — `$CHUNK_PLAN` is the sole driver of `$CHUNK_FILES_i` and `$FILES_BLOCK_i`, so an empty/missing plan means there is nothing to bind the per-chunk prompts to. STOP and print "I'm uncertain about Phase 2 (`--all` per-chunk dispatch) — `$CHUNK_PLAN` was not produced by Phase 0.2; refusing to dispatch with undefined chunk variables." per the HARD CONTRACT's surface-the-uncertainty rule. Do NOT silently fall back to a whole-set `$REVIEW_SET` dispatch (that would defeat per-chunk triage CHUNK-03 and the budget/order guarantees) and do NOT dispatch with undefined `$CHUNK_FILES_i`/`$FILES_BLOCK_i`. (The empty-`$REVIEW_SET` case is already handled upstream by the Phase-0 mode-5 empty-set guard, so a populated `$REVIEW_SET` with no `$CHUNK_PLAN` indicates Phase 0.2 did not run — the numerical-order bug this guard backstops.)

For chunk `i` (i = 1..K, riskiest first):

1. **(triage turn)** Run chunk `i`'s per-chunk triage FIRST over `$CHUNK_FILES_i` (Phase 1, Site B — the `--all` per-chunk triage step in `10-triage.md`): one Task call to the `triage` agent on chunk `i`'s files, yielding `languages_i` / `frameworks_i` / `total_lines_i` / `size_tier_i` / `files_to_skip_i`.
2. **(filter)** Apply chunk `i`'s triage `files_to_skip_i` to the chunk — the per-chunk analog of diff-mode's Phase-1→Phase-2 `files_to_skip` exclusion (which stays unchanged): derive `$CHUNK_REVIEW_FILES_i = $CHUNK_FILES_i` MINUS the paths in `files_to_skip_i` (exact full-path match, lexicographic order preserved). Everything downstream for chunk `i` — `$FILES_BLOCK_i`, the `<changed-files>`/`{{filtered_file_list}}` binding, AND the per-chunk line/byte totals used by the Phase-4 reviewed-partial trigger — is built from this FILTERED `$CHUNK_REVIEW_FILES_i`, NEVER from the raw `$CHUNK_FILES_i`. A file the chunk's triage marked generated/minified/binary/skippable is thus NOT sent to any reviewer agent for that chunk, and coverage is not spent on it (CHUNK-03 intent: per-chunk triage gates what each chunk dispatches). **Empty-after-filter:** if filtering empties the chunk (`files_to_skip_i` covers every file in `$CHUNK_FILES_i`), SKIP chunk `i` entirely — do NOT build an empty `$FILES_BLOCK_i` and do NOT dispatch any agents for it; note it (`✓ Phase 2 (chunk i/<K>) — all files skipped by triage, nothing to dispatch`) and CONTINUE to chunk `i+1`. The per-chunk line/byte totals recomputed off `$CHUNK_REVIEW_FILES_i` (sum of the surviving files' totals from `$CHUNK_PLAN`) are what Phase 4 reads, so a skipped file never inflates the partial-coverage gate either.
3. **(build turn)** Build `$FILES_BLOCK_i` ONCE for chunk `i` from `$CHUNK_REVIEW_FILES_i` (the skip-filtered list from step 2), lexicographic WITHIN the chunk, reusing the `<files>` block format above VERBATIM (the D-07 per-file fenced-block format — do NOT redefine it; just scope it to chunk `i`'s surviving files). This block build is a PRIOR turn (Bash/reasoning) — it MUST live in a turn BEFORE chunk `i`'s fan-out turn, never in the fan-out turn itself (the D-08 one-turn-pure-dispatch rule, restated per chunk).
4. **(select)** Select chunk `i`'s agents via the EXISTING selection table in `20-dispatch.md` (input = chunk `i`'s triage result): `bugs`+`security` always; `language-*`/`framework-*` per `languages_i`/`frameworks_i`; `compliance` if `CLAUDE.md`/`AGENTS.md` present; deep mode (`/deep-review`) adds `architecture`+`impact` (D-04). Announce `✓ Phase 2 (chunk i/<K>) — Dispatching N_i agents in parallel: [list]`.
5. **(fan-out turn)** ONE assistant turn = N_i parallel `Task` calls over chunk `i`'s `$FILES_BLOCK_i`, zero other tool calls — the MANDATORY DISPATCH SHAPE preserved PER CHUNK. Bind BOTH prompt halves to chunk `i`'s FILTERED list per the **Per-chunk binding override** above: `{{git_diff_output}}` ← `$FILES_BLOCK_i` (built from `$CHUNK_REVIEW_FILES_i`) AND `{{filtered_file_list}}`/`<changed-files>` ← `$CHUNK_REVIEW_FILES_i` (the skip-filtered list, NEVER the raw `$CHUNK_FILES_i` and NEVER `$REVIEW_SET`). Position-stability per chunk: `$FILES_BLOCK_i` is IDENTICAL across chunk `i`'s N_i agent calls; only the agent-name sentence (+ intent-context for architecture/compliance) differs.
6. **(accumulate)** After chunk `i`'s N_i Task calls return, ACCUMULATE the N_i responses into the run-level `AGENT_RESPONSES` set and MOVE TO THE NEXT CHUNK — do **NOT** proceed to Phase 3 yet.

**Loop exit → Phase 3 runs ONCE over the accumulated `AGENT_RESPONSES`.** After the LAST chunk accumulates, the loop completes; Phase 3 (collect/verify/dedup/score) then runs EXACTLY ONCE over `AGENT_RESPONSES` (the union across all chunks) — never inside the loop, never per chunk. This is the load-bearing seam: Phase 3 must see all chunks at once so cross-chunk dedup/score (and Phase 10's later merge) work. `agents_run` in the persisted pass entry becomes the UNION of agents dispatched across all chunks (field shape unchanged).

**Both legacy Phase-3 hand-offs are SUPERSEDED in `--all` (Codex round-1 Finding 1):** the MANDATORY-DISPATCH-SHAPE "the next assistant turn … is Phase 3" sentence AND the "After they all return, proceed to Phase 3" line (both in `20-dispatch.md`) are the SINGLE-dispatch (diff-mode) shape. Both carry an `$ALL_MODE` accumulate-and-continue override: in `--all` the post-fan-out turn accumulates into `AGENT_RESPONSES` and continues the loop; Phase 3 runs ONCE after the loop. Neither "Phase 3" sentence is reachable per-chunk in `--all`.

🚫 **ANTI-PATTERN (Codex round-1 Finding 1; `08-RESEARCH.md` Pitfall 1):** Do NOT run Phase 3 inside the loop — Phase 3 runs ONCE after ALL chunks accumulate; per-chunk Phase 3 breaks cross-chunk dedup (Phase 10) and fragments scoring (a `--all` run rendering K separate reports is the warning sign). Both the "next assistant turn … is Phase 3" sentence and the "proceed to Phase 3" line are SUPERSEDED in `--all` by the accumulate-and-continue override above.

🚫 **ANTI-PATTERN (D-05/D-08; `08-RESEARCH.md` Pitfall 3):** Do NOT split a chunk's fan-out across turns — each chunk's dispatch is still ONE pure-Task turn (N_i parallel Task calls, zero other tool calls). Looping sequentially ACROSS chunks is correct; splitting WITHIN a chunk (e.g. building `$FILES_BLOCK_i` or reading files in the same turn as the Task calls) is the anti-pattern — build the block and select agents in PRIOR turns.
