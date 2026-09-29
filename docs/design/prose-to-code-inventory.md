# vibe-check — Deterministic-Prose Extraction Inventory

> **Status:** Opus, 2026-07-01. The definitive inventory of deterministic logic that currently
> lives as prose/bash in the command + agent files and is a candidate for extraction into
> tested Python (like the existing `scripts/score.py` / `scripts/config.py`). Built from a
> full read of `review.md` (1068 lines), `deep-review.md` (379), `fix.md`, `codex-adversarial.md`.
>
> This exists because the "prose that should be code" question (raised by external feedback via
> O1) turned out to be much larger than the containment guard alone — but it also does NOT mean
> "convert everything." The value is the **per-block extract-vs-keep judgment**, especially the
> cost side. Feeds hypothesis **O-EXTRACT** in `design-hypotheses.md`.

## The organizing insight

~30 deterministic prose blocks exist, but they consolidate into **three extraction families**
that hold nearly all the leverage — plus a set of blocks that should deliberately STAY prose
because extracting them adds coupling that costs more than it saves. The job is not "scriptify
everything"; it's "extract the three families, leave the rest, and know why."

Already extracted (done, not candidates): `score.py` owns stable_hash, silenced_nearby,
carry_forward_status, compute_score, cross-confirm grouping, band_for, _line_in_ranges,
min_confidence filter. `config.py` owns the `.vibe-check.toml` reader + validation.

---

## The three extraction families (ranked — this is where the work is)

### Family 1 — Path validation (HIGHEST: security boundary, worst drift surface)
A `validate_repo_path(path, root, allow_glob=)` module collapsing three duplicated primitives:
- **realpath-containment guard** — `review.md:130-138, 177-198` (BSD-realpath Python-heredoc
  variant), `deep-review.md:138, 329-344`, `fix.md:28`, `codex-adversarial.md:95-106`.
  **5 files, ≥6 hand-copied sites, already diverging.**
- **path regex allowlist** (`^[A-Za-z0-9._/-]+$`, glob variant) — `review.md:114, 172-175`,
  `deep-review.md:321-328`, `fix.md:28`, `codex-adversarial.md:97-100`.
- **explicit `..` / pathspec-magic reject** (`:(top)`, `:!`, `:^` arms) — `review.md:161-170`
  (superset), `deep-review.md:321-327`. **The two copies already differ** — review.md carries
  pathspec-magic arms the others lack. Drift has begun.
- **Why highest:** it's a security boundary (traversal / symlink escape / pathspec-magic
  audit-scope injection), relied on by every mode + both commands + the fix agent, with the
  worst drift surface in the repo. The tool auto-commits, so a containment miss = write outside
  the repo.

### Family 2 — Chunk-packer + risk math (PUREST: free win, high reliance)
A `risk_rank_and_pack(files_with_sizes)` module (golden-tested like `score.py`):
- **path-tier risk classifier** (path → tier 0-3) — `review.md:245-258`, pure pattern→int.
- **risk-sort + key assembly** (`sort -k1,1n -k2,2nr`) — `review.md:260, 264-269`; the sort-key
  order IS the CHUNK-01 anti-pattern the prose warns about (`:271`).
- **chunk packer** (seed + same-dir fill + spill, dual line/byte budget) — `review.md:277-306`.
  **The purest input→output logic in the repo** (prose literally calls it "DETERMINISTIC" /
  "reproducible" at `:277`); documented edge case A (oversized single file, `:289`).
- **overflow / reviewed-partial trigger** — `review.md:891-899` (shares the 1800/200000 bounds).
- **budget COUNTS** (source/chunk/agent-floor/dispatch-upper) — `review.md:318-329` (the exact
  counts only — NOT the cost bracket, see keep-list).
- **Why:** purest and most testable; feeds three downstream consumers via the `$CHUNK_PLAN`
  contract, so an error propagates widely. Low coupling — consumes an already-materialized list.

### Family 3 — Codex output sanitization (SECURITY: highest-consequence copy-paste)
A `sanitize_codex_output()` (title + note-cap + field translation):
- **title sanitization** (strip bidi U+202A-E / U+2066-9, zero-width U+200B-D/FEFF, U+2028-9,
  control chars, backticks; single-line) — `codex-adversarial.md:110-122`, **restated verbatim**
  `deep-review.md:313-314`; related stricter cousin `fix.md:29`. Unicode codepoint list re-typed
  across 2 files.
- **note cap** (first-newline + 300-char) — `codex-adversarial.md:32,44`, `deep-review.md:313,317`.
- **field-translation map** (Codex keys → vibe-check schema) — `codex-adversarial.md:48-60`,
  restated `deep-review.md:313`.
- **Why:** security-relevant (prompt-injection / trailer-forgery / RTL-override spoofing into
  an autonomous fix agent that writes + commits code); the exact codepoint list is duplicated;
  `fix.md:29` keeps a deliberately *different* allowlist the doc flags as load-bearing.

---

## Second-tier extraction candidates (real, lower leverage)

| Block | Location | Extract-vs-keep |
|---|---|---|
| commit-message construction (`printf` + `-F msgfile` + `--cleanup=verbatim` + `--`) | `fix.md:32-51`, restated `review.md:1032-1035` | **Extract** `commit_fix()` — review.md:1033 literally says "copy it in full" = drift admission |
| commit title-sanitization allowlist (`[A-Za-z0-9 ._:/()#=-]`) | `fix.md:29` | **Extract** — pairs with commit_fix; pins the trailer-forgery guard |
| plugin-script resolver (working-tree → cache `sort -V` glob → marketplace) | `review.md:774-799, 442-462`, `deep-review.md:226-238` | **Bash template, NOT Python** — chicken-and-egg (see keep-list); 3 copies, 1 intentional inversion |
| codex diff-representability gate (representable range == Phase-0 diff) | `deep-review.md:245-259` | **Extract the predicate** — dense, safety-critical |
| symlink (mode-120000) filter + selection | `review.md:206-213` | **Extract** `ls-files → (regular, symlink_count)` — feeds chunker |
| skip-rules matcher (data is templated; engine is prose) | `review.md:215-217` | **Extract the matcher** `apply_skip_rules(files, include_docs)` |
| state-file path resolution per mode + scope-hash | `review.md:382-398` | **Extract** `state_path()` — "comment must match code" invariant is a drift smell |
| finalize gate (outstanding C/W + unack-medium) | `review.md:32-47` | **Extract** — pure filter over parsed state |
| coverage R/T/S arithmetic + symlink separation | `review.md:882-889` | **Extract** — the R+S=T invariant fixes a known past bug |
| cross-file dedup render grouping (Jaccard ≥0.7) | `review.md:907-913` | **Extract** — pure grouping, pinnable threshold |
| `<files>` block builder + ext→fence map | `review.md:686-701` | **Extract with care** — output must survive the boundary byte-identical (cache) |

---

## The KEEP list — extraction would COST more than it saves (the important half)

These are deterministic but should stay prose/bash. Naming them prevents an over-eager
"scriptify everything" pass from breaking things:

- **One-pass churn table** (`review.md:241`) — the prose deliberately chose ONE `git log | sort
  | uniq -c` over N per-file calls for cost. Extract the *ranking math* (Family 2), but the git
  call stays glue; piping the raw table into a script adds a serialization boundary for no gain.
- **`wc -l` / `wc -c` size measurement** (`review.md:260, 264`) — the "single measurement
  source." Moving it into a script forces file I/O into what is otherwise a pure scorer,
  breaking `score.py`'s explicit no-git/file/shell-I/O purity (`:759`). Keep sizes
  orchestrator-measured; pass them into the pure packer as data.
- **`--all` cost bracket + time band** (`review.md:328-329`) — deliberately fuzzy (D-01: "never
  a bare point figure"), hard-coded model prices. Extract the *counts*, keep the *ranges* prose
  — scripting a number meant to stay loose adds a price-table maintenance burden.
- **Plugin-script resolver** (`review.md:774-799` etc.) — **cannot** be a Python helper:
  chicken-and-egg (you need the resolver to find the helper). The fix is a shared *bash
  template*, not an extract; its deliberate terminal-arm inversion (config.py degrades,
  score.py fails-closed) must be a preserved parameter, not flattened.
- **`<files>` block cache-stability** — extractable functionally, but the returned string must
  be spliced byte-identically across a chunk's N prompts or prompt-caching breaks. A "value must
  survive the boundary unchanged" coupling, not a clean win.
- **Trivial one-liners** — codex confidence `round(x*100)`, verdict→findings branch, `--all`
  flag parse, reviews/ dir prune, `--min-confidence` arg-scrape (validation already in
  config.py). Not worth a shell-out; low drift.

---

## How this routes into the Fable review

This inventory is the evidence base for **O-EXTRACT** (`design-hypotheses.md` §A). Fable's job
is NOT to accept "extract these" — it's to stress-test the *judgment*: for each family, does the
correctness/drift win justify the shell-out coupling, and is the keep-list correct (did we wrongly
keep something that's actually a latent bug, or wrongly extract something with hidden coupling)?
The B1 code-review pass (smell #7) attacks the same prose as *code* — can a crafted input defeat
the containment or sanitization while it's still prose?

The falsifiable form per family:
- **Family 1:** exhibit a path (symlink / `..` variant / glob-prefix escape / pathspec-magic)
  that one of the ≥6 copies handles differently than another → proves the drift is live, not
  theoretical.
- **Family 2:** exhibit a file set where the prose packer plausibly mis-ranks or mis-packs
  (CHUNK-01 sort-key, edge-case-A) in a way a tested unit would catch.
- **Family 3:** exhibit a codex output (RTL override, zero-width injection, >300-char note)
  that the two hand-copies sanitize differently.

---

## Phase 40 reconciliation (v2.10)

Appended at the close of v2.10 Phase 40. The ranked families, the second tier and the KEEP list
above are left as they were written. This section records what the phase did with them.

**How it was checked before it was written (F7, FL-13).** The following loop ran against the tree
at `1f91df8` and passed for all nine modules. For each module it checks three things: the script
exists under `plugins/vibe-check/scripts/`, its `test_<name>.py` sits beside it, and `<name>.py` is
referenced under `plugins/vibe-check/phases/`. A failure prints `MISSING SCRIPT`, `MISSING TEST` or
`BUILT BUT NOT WIRED` and exits non-zero.

```bash
for m in chunks select_files codex_translate codex_gate fixcommit coverage dedup statepath \
         finalize_gate; do
  test -f "plugins/vibe-check/scripts/$m.py"      || { echo "MISSING SCRIPT $m"; exit 1; }
  test -f "plugins/vibe-check/scripts/test_$m.py" || { echo "MISSING TEST $m"; exit 1; }
  grep -rq "$m.py" plugins/vibe-check/phases/     || { echo "BUILT BUT NOT WIRED $m"; exit 1; }
done
```

The loop's reference check is loose. For `coverage`, one of its two matches is
`01d-coverage.md:24`, which names the unrelated Python `coverage.py` tool. So each row below also
names the file with a real `python3 "$VC_ROOT/scripts/<name>.py"` invocation. A stricter grep for
that exact form found an invocation for all nine modules.

### Extracted and wired

| D-07 item | Script | Invoked from (`phases/`) |
|---|---|---|
| F1: path validation (pre-phase, `18f3c6c`) | `guard.py` | `shared/01-bootstrap.md` |
| F2: chunk packer + risk math | `chunks.py` | `review/02-chunk-plan.md (+2)` |
| `--all` symlink (mode-120000) filter | `select_files.py` | `review/00-scope-all.md` |
| skip-rules matcher | `select_files.py` | `review/00-scope-all.md` |
| F3: codex output sanitization | `codex_translate.py` | `deep-review/30-codex-collect.md` |
| codex diff-representability | `codex_gate.py` | `deep-review/2c-codex-kickoff.md` |
| commit message + title allowlist | `fixcommit.py` | `review/50-fix-loop.md` |
| per-mode state-path resolution | `statepath.py` | `review/05-state-all.md` |
| finalize gate | `finalize_gate.py` | `shared/90-finalize.md` |
| coverage R/T/S arithmetic | `coverage.py` | `review/40-render-all.md` |
| cross-file dedup grouping | `dedup.py` | `review/40-render-all.md` |

Every script above is locked by the `test_<name>.py` beside it in `plugins/vibe-check/scripts/`
(`test_guard.py`, `test_chunks.py`, `test_select_files.py`, `test_codex_translate.py`,
`test_codex_gate.py`, `test_fixcommit.py`, `test_statepath.py`, `test_finalize_gate.py`,
`test_coverage.py`, `test_dedup.py`); the loop above asserts each one exists. F1-F3 are the ranked
Families 1-3.

Wired by: `fixcommit.py` in 40-07; `codex_translate.py` and `codex_gate.py` in 40-11; the rest in
40-10. `chunks.py` is also invoked from `review/03-estimate-gate.md` and `review/40-render-all.md`.
`guard.py` is resolved once in the bootstrap as `$GUARD_PY` and used from the scope and coverage
files.

### Keep-list confirmed still prose (D-08)

| Kept as prose | Where it lives now (`phases/`) |
|---|---|
| `<files>` block builder + ext→fence map | `review/20-dispatch-all.md` |
| report rendering | `review/40-render.md`, `review/40-render-all.md` |
| one-pass churn table (the git call; ranking math is `chunks.py`) | `review/02-chunk-plan.md` |
| `wc -l` / `wc -c` size measurement | `review/02-chunk-plan.md`, `review/10-triage.md` |
| `--all` cost bracket + time band ranges | `review/03-estimate-gate.md` |
| plugin-script resolver (the TRUST-01 bash template) | `shared/01-bootstrap.md` |

**Coverage and dedup boundary.** The arithmetic (R/T/S buckets, skip reasons) and the grouping rule
are extracted into `coverage.py` and `dedup.py`. How the numbers and groups are presented stays
prose in `review/40-render-all.md`. That split satisfies both D-07 (extract the deterministic part)
and D-08 (keep rendering as prose).

DIET-02's settled scope shipped complete, because the check above passed. Nothing is left unbuilt.

### Phase-exit record (DIET-04 end-of-phase check)

Transcribed from `docs/design/b3-ground-truth/runs-v2.10-phase40/final/PASS.json`: verdict `PASS`,
adjudicated in `330ad0e`, snapshot `batch3-e79bff32c01f`. `batchsnap.py check-pass` validated it at
the phase-close barrier. The batch-3 artifact (`batch3/PASS.json`, `9fcd69f`) also validated.

The six runs and their adjudications: `triggarr-secret-in-logs` run-1 catch, run-2 catch, run-3
catch; `should-quiet-5` run-1 clean, run-2 clean, run-3 clean.

- **DIET-04 gate:** `triggarr-secret-in-logs` **3/3 catch** against its Phase-38 baseline of 3/3,
  so catch-rate is no worse. The site (`base.py` 230-238 / 249-256) and axis (credentials and API
  keys written to logs, CWE-532) were met in every run.
- **For information only:** `should-quiet-5` **0/3 FP** (Phase-38 triplet: 1/3 FP). Each run
  reported 0 findings. Phase 43 is the real false-positive proof.

**Measurement conditions** (from the artifact's `adjudication_note`, quoted):

- "both clone projects' Claude Code auto-memory PARKED per runbook N-02"
- Codex: "sil 1/2/3 JOINED (needs-attention,1 each); sq5 1 SKIPPED (unavailable: launch gate
  wants BashOutput, absent in CC 2.1.281), sq5 2 JOINED (approve), sq5 3 SKIPPED —
  improvisation-dependent gate, plugin fix deferred (see 40 deferred-items)". Here "sil" is
  `triggarr-secret-in-logs` and "sq5" is `should-quiet-5`. This plugin defect was deferred, not
  fixed in Phase 40.
- "Usage-limit pause 21:33-22:50 during sil run 1 (after report rendered) and sq5 run 2 (before
  dispatch); both auto-resumed in place, not voided."
