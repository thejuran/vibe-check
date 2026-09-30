# Phase 4.5 — Persist pass state

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 4.5 is entered (every review, immediately after Phase 4).
> Announce on entry, after this Read: `✓ Phase 4.5 — Persist pass state`.

Use the stable_hash the script already computed — consume the `stable_hash` field `scripts/score.py` returned on each survivor finding in Phase 3, and do NOT recompute the sha256 by hand. `scripts/score.py` is the single writer of the scored fields (`orchestrator_score`/`band`/`status`/`stable_hash`/`attribution`), preserving single-writer (ROBUST-01); reintroducing a by-hand hash here would create a second writer and risk drift that silently breaks `medium_acknowledgments[stable_hash]` lookups. The pass-entry build below and the `findings: [...]` slot consume the script's enriched output unchanged — no field is renamed or dropped, so the finding shape stays byte-shape-identical (Finalize's band ∈ {critical,warning} reads and the `medium_acknowledgments[stable_hash]` lookup keep working).

Build pass entry. **This is the pass-entry key set, stated ONCE** — Phase 4.5 is the single writer of the pass entry (W1). Its machine copy is `scripts/fixtures/future-schema.json`, which `scripts/state_shape.py --schema future` enforces: the nine keys below are all REQUIRED in every pass, no other key is allowed, and the three `--all` keys are the only additions an `--all` run may make. Where this prose and that schema ever disagree, the schema wins.

````json
{
  "pass_number": $PASS_NUMBER,
  "head_sha": "<current HEAD>",
  "timestamp": "<UTC, second resolution: YYYY-MM-DDTHH:MM:SSZ>",
  "mode": "review",
  "diff_range": "<resolved range>",
  "agents_run": [<dispatched agents>],
  "findings": [...],
  "filtered": [...],
  "codex": {"status": "<joined|skipped|off>", "reason": <slug|null>, "verdict": <"approve"|"needs-attention"|null>, "findings": <int>}
  // --all ONLY (omit these three keys ENTIRELY in diff mode — diff-mode pass-entry shape is byte-unchanged):
  //   "cap_applied": $K_OR_NULL,        // K, or null on a Run-full run; $K_OR_NULL/$N are bound only inside the --all Phase 0.3 gate
  //   "chunk_total": $N,
  //   "capped_chunks": [<chunks K+1..N: per-chunk identity + file list, or null on a Run-full run>]
}
````

**Field values — the canonical form of every key whose value is not copied straight from Phase 3.**

| Key | Canonical value | Serialized as |
|---|---|---|
| `timestamp` | the write time in UTC, to the second | the string `YYYY-MM-DDTHH:MM:SSZ`, produced by `date -u +%Y-%m-%dT%H:%M:%SZ` — never fractional seconds, never a `+00:00` offset |
| `mode` | `review` for `/review`; `deep` for `/deep-review` | JSON string |
| `findings` | `scripts/score.py`'s returned `findings` array, unchanged | JSON array |
| `filtered` | `scripts/score.py`'s returned `filtered` array (`{file,line,title,reason}` each), unchanged — `[]` when nothing was filtered | JSON array |
| `codex.status` | `joined` — Codex ran and its translated response joined the agent-response set at Phase 3 entry (a zero-finding `approve` counts as joined); `skipped` — Codex was in play but did not join (a `scripts/codex_gate.py` skip, or the collection-time `timeout`); `off` — Codex was not in play: `/review` never runs it, and `/deep-review` with `$CONFIG_CODEX` resolved to `off` | JSON string, exactly one of the three |
| `codex.reason` | `skipped` → the slug that decided the skip, one of `scripts/codex_gate.py`'s `SLUGS` (`not-installed`, `unauthenticated`, `unavailable`, `whole-repo-non-representable`, `phase-diff-has-uncommitted-tail`, `range-not-identical`, `head-not-at-target`, `no-timeout-binary`, `focus-unreadable`, `timeout`); `joined` / `off` → null | a lowercase hyphenated slug string, or `null` — never free text |
| `codex.verdict` | `joined` → Codex's own `verdict` (`approve` or `needs-attention`); `skipped` / `off` → null | JSON string or `null` |
| `codex.findings` | `joined` → the number of translated Codex findings that joined at Phase 3 entry (before scoring; `0` on `approve`); `skipped` / `off` → `0` | JSON integer — never a string, never `null` |

The `codex` record has exactly these four keys and no others. A `/review` pass therefore always writes `"codex": {"status": "off", "reason": null, "verdict": null, "findings": 0}`. Nothing else goes into the pass entry — no notes, no counters, no extra flags; anything worth saying about the run belongs in the chat transcript.

If `$ALL_MODE` is set, **Read $VC_ROOT/phases/review/45-persist-all.md** with the Read tool before continuing — it adds the capped-run facts to THIS pass entry. On a plain diff review, do not read it.

**New state file.** If the state file does not exist yet, create it with this exact root, then append the pass entry to its `passes` array. Both root keys are REQUIRED by `scripts/fixtures/future-schema.json` (`root_required`), and no other root key is allowed:

````json
{
  "medium_acknowledgments": {},
  "passes": []
}
````

`medium_acknowledgments` is a JSON object (never an array, never omitted), keyed by a finding's `stable_hash` — Finalize writes each dismissal into it (`phases/shared/90-finalize.md`). A fresh state starts it as the empty object `{}`.

**Existing state file.** Keep every root key it already has, unchanged — never drop, rename, or reset `medium_acknowledgments`. If an older file lacks `medium_acknowledgments`, add it as `{}`.

Append to `state.passes`, write to state file. Create parent dirs as needed (`.turingmind/state/`).

Optional: snapshot this run for debugging:
```bash
RUN_DIR=".turingmind/reviews/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_DIR"
# Write: diff.patch, agents-dispatched.txt, findings.json
```

Then prune: keep last 10 dirs under `.turingmind/reviews/`, delete older:
```bash
ls -t .turingmind/reviews/ 2>/dev/null | tail -n +11 | xargs -I {} rm -rf ".turingmind/reviews/{}"
```

**→ Proceed immediately to Phase 5 (Interactive fix loop). Do not stop here. State has been persisted; the user is still in the conversation waiting for the AskUserQuestion that Phase 5 dispatches. Skipping Phase 5 means the user has to manually invoke the command again to engage the fix workflow — that's a contract violation.**
