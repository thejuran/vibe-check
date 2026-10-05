# Phase 1 — Triage

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 1 is entered (every review).
> Announce on entry, after this Read: `✓ Phase 1 — Triage`.

**Git-safety snapshot (FIX-03, D-10) — its own Bash call, BEFORE the triage Task, once per pass.** Review agents must leave the reviewed repo's git state alone. Before any agent runs, fingerprint that state and clear the block records left by an earlier pass; Phase 3 compares against this snapshot when every agent has returned.

```bash
GREPO=$(git rev-parse --show-toplevel 2>/dev/null)
if python3 "$VC_ROOT/scripts/gitsnap.py" take --root "$GREPO" --out "$GREPO/.turingmind/git-guard/before.json" && python3 "$VC_ROOT/scripts/gitguard.py" reset --root "$GREPO"; then
  echo "git-safety snapshot taken"
else
  echo "git-safety snapshot could not be taken — review HALTED before any agent ran" >&2
fi
```

- Run it in its own turn — never in the turn that dispatches the triage Task.
- On the else branch, print `git-safety snapshot could not be taken — review HALTED before any agent ran` as message text and STOP the review: dispatch no agent and do not continue to any later phase. This fails closed — without a snapshot the pass cannot prove the repo was left alone.
- In `--all` mode take it ONCE, before the first chunk's triage — never once per chunk. The comparison in Phase 3 covers the whole pass.
- `--finalize` dispatches no agents and never reaches this phase, so it takes no snapshot.

Dispatch a single Task call to `triage` agent. Prompt:

````
You are the triage agent. Classify this diff.

<diff-stat>
{{git diff --stat <range>}}
</diff-stat>

<changed-files>
{{git diff --name-only output}}
</changed-files>

<repo-root-files>
{{ls of repo root, immediate level}}
</repo-root-files>

{{if $PHASE_ID set: <phase-dir>{{$PHASE_DIR}}/</phase-dir>}}

Return JSON per your subagent instructions.
````

**`--all` mode (`$ALL_MODE` set) — per-chunk triage (CHUNK-03; additive, diff-mode prose above byte-unchanged):** there is no diff, so triage runs **ONCE PER CHUNK** over THAT chunk's files — NOT once over the whole `$REVIEW_SET`. A chunk is just a smaller whole-file set, exactly the contract `agents/triage.md` already satisfies; triage already derives `languages` from file extensions and `frameworks` from imports (both work on whole files), so `agents/triage.md` itself needs NO edit.

**Precondition (`$ALL_MODE` set):** per-chunk triage consumes `$CHUNK_PLAN`, which Phase 0.2 (numbered to run before this phase) must already have produced and which must be non-empty. If `$ALL_MODE` is set but `$CHUNK_PLAN` is unset/empty when triage is reached, do NOT triage the whole `$REVIEW_SET` as a fallback (that reintroduces the CHUNK-03 anti-pattern); the Phase-2 per-chunk dispatch loop's own `$CHUNK_PLAN` precondition guard (Site C, below) is the single STOP/uncertainty point — defer to it rather than improvising here.

For chunk `i` of `$CHUNK_PLAN` (i = 1..K, riskiest chunk first — K is the Phase-0.3 gate's chosen cap; Run full sets K = N):

- **`<changed-files>` ← `$CHUNK_FILES_i`** — the ordered file list of the CURRENT chunk (one element of `$CHUNK_PLAN`), NEVER `$REVIEW_SET`. This is the same `$CHUNK_FILES_i` name the Phase-2 per-chunk dispatch loop (Site C, below) and its `{{filtered_file_list}}`/`<changed-files>` binding use — all three sites bind to the SAME per-chunk file list.
- **`<diff-stat>` ← chunk `i`'s per-file LINE-COUNT stat** — render a `file<TAB>lines` block for chunk `i` from the per-file LINE totals `$CHUNK_PLAN` already carries (the `wc -l` size column computed once in Phase 0.2 / step 0.2a). Do NOT downgrade this to a bare `git ls-files` file count: `agents/triage.md` derives `total_lines`/`size_tier` from LINE counts, so a bare file count would make those fields meaningless per chunk; the per-chunk line stat keeps `total_lines`/`size_tier` valid for chunk `i`. (Note: Phase 4's reviewed-partial trigger reads `$CHUNK_PLAN`'s per-chunk line total DIRECTLY for determinism — but keeping triage's per-chunk line stat valid is still correct and cheap.)

Keep the rest of the prompt as-is. The per-chunk triage call is the FIRST step inside the `$CHUNK_PLAN` loop: for chunk `i`, dispatch triage on `$CHUNK_FILES_i` → `languages_i` / `frameworks_i` / `total_lines_i` / `size_tier_i`. That per-chunk output drives THAT chunk's agent selection via the EXISTING selection table (below, unchanged in shape): `bugs`+`security` fire on EVERY chunk; `language-*`/`framework-*` fire ONLY on chunks where that language/framework appears (per `languages_i`/`frameworks_i` derived from `$CHUNK_FILES_i`); `compliance` fires when `CLAUDE.md`/`AGENTS.md` is present (D-04). Only the table's INPUT changes (the chunk's triage result, not the whole-set result) — the table itself is NOT rewritten. The loop body (triage-per-chunk → dispatch-per-chunk) lives in Phase 2 (Site C, the per-chunk dispatch loop) — triage-per-chunk and dispatch-per-chunk are the SAME loop.

🚫 **ANTI-PATTERN (CHUNK-03; `08-RESEARCH.md` Per-Chunk Triage):** Do NOT feed per-chunk triage the whole `$REVIEW_SET` — each chunk's triage input is `$CHUNK_FILES_i` (that chunk's files only), with the chunk's per-file LINE stat for `<diff-stat>`. Using `$REVIEW_SET` makes a markdown-only chunk inherit the whole repo's languages/frameworks and dispatch `language-python`/etc. it has no business running (breaks CHUNK-03); a bare file count breaks triage's `total_lines`/`size_tier`.

**`--all` mode (`$ALL_MODE` set) — SKIP this single-response parse/use tail.** In `--all` mode there is NO single whole-set triage response at this point: triage moved INTO the per-chunk loop (the per-chunk triage step above + the Phase 2 per-chunk dispatch loop), so there is nothing to parse here. SKIP the single-response `Parse JSON. Use:` block below entirely. Per-chunk agent selection, `files_to_skip`, and `size_tier` are driven by EACH chunk's OWN triage result (`languages_i`/`frameworks_i`/`size_tier_i` from `$CHUNK_FILES_i`), consumed inside the Phase 2 per-chunk dispatch loop — NOT from a whole-set parse here. (`intent_docs_found` → Phase 1.5 is moot in `--all`: Phase 1.5 only runs when `$PHASE_ID` is set, and `--all` leaves `$PHASE_ID` unset — see Phase 0 mode 5 step e.) Do NOT parse or use undefined/stale single-triage values for agent selection or model downgrades in `--all`.

**Diff mode (`$ALL_MODE` NOT set) — parse the single triage response as before (byte-unchanged):**

Parse JSON. Use:
- `languages` + `frameworks` → Phase 2 agent selection
- `files_to_skip` → exclude from diff sent to other agents
- `size_tier` → large-diff auto-downgrade in Phase 2
- `intent_docs_found` → Phase 1.5 (M6)
