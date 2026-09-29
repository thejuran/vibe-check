# Prose diet — per-mode footprint, before and after (v2.10 Phase 40, DIET-01)

**Headline: the plain review path's prose fell 41.7% by bytes and by both proxies (189,625 →
110,616 bytes). Measured tokens were taken for the BEFORE leg only.** That is past the 40% soft
target. The target was never a gate, and no prose was cut to reach it (§4).

## 1. How to read this

**Where every stats row comes from.** Every bytes, words and proxy figure below comes from
`plugins/vibe-check/scripts/footprint.py` output. Nothing here is re-derived by hand.

- **BEFORE** rows are captioned revision **`7a386ed`** (`PRE_PHASE_REV`, the pre-phase pin). They
  are transcribed from the run that plan 40-05 recorded against the pre-phase `MODE_PATHS` inventory
  (`footprint.py --rev 7a386ed --json`, 2026-09-08). They are **not recomputed here**.
- **AFTER** rows come from a fresh `footprint.py --json` run against the post-phase `MODE_PATHS`, on
  the worktree at commit `330ad0e`. The plugin's command and phase prose last changed at `d05ecb6`,
  and `commands/` plus `phases/` are byte-identical to the batch-3 snapshot `e79bff3` that the
  owner's final runs used.

**Do not re-run the BEFORE leg.** `MODE_PATHS` is a live table. Plans 40-08, 40-10 and 40-11 each
rewrote it to point at the post-restructure spines and `phases/**` files. Running the rewritten
table against `7a386ed` asks `git show 7a386ed:<path>` for files that did not exist at that
revision. They land in `missing`, `path_stats` degrades (D-13) and still returns, and the command
exits 0 with only a stderr warning. The result silently undercounts. `deep-plain` would report
84,534 bytes (`deep-review.md` alone) instead of the true 274,159, because the rewritten entry no
longer names `commands/review.md`. That is 189,625 bytes missing. (`git show 7a386ed:…/review.md |
wc -c` gives 189,625, and the deep monolith gives 84,534; 189,625 + 84,534 = 274,159.) A pinned
measurement recomputed later against a changed inventory is not the same measurement. The recorded
one is the BEFORE figure.

**Which numbers are measured, and how.** The `measured (harness delta)` column is the only
observation of tokens. The method (RESEARCH Q10, 2026-09-08): nested `claude -p --output-format
json`, model `claude-sonnet-5`, `--max-turns 1 --allowedTools ""`, the file body as the prompt, an
empty-body baseline of **44,721** input tokens subtracted, 3 runs. The BEFORE figures are **79,954**
(`commands/review.md`, 2.37 bytes/token) and **35,393** (`commands/deep-review.md`, 2.39
bytes/token). The deep path read both files, so **115,347** is its BEFORE figure. These match the
ROADMAP's "~80K / ~35K".

**Word counts are locale-independent** (40-05's decision). BSD `wc -w` under `en_US.UTF-8` gives
27,148 / 12,134 for the two monoliths. `footprint.py` gives 27,146 / 12,132 in every locale. The
table uses the `footprint.py` figures. Byte counts do not depend on locale.

## 2. The footprint table

Every mode path has a BEFORE row (`7a386ed`, from 40-05's recorded run) and an AFTER row (worktree
at `330ad0e`, fresh run). The table is split in two only to stay within the 100-column wrap. Table A
holds the stats and both labelled proxies. Table B holds the measured column and the change.

**Table A — stats, from `footprint.py`**

| mode path | leg | bytes | words | tokens@3.5 (proxy, legacy) | tokens@2.7 (proxy, D-11 restated) |
|---|---|---|---|---|---|
| `review-plain` | before | 189,625 | 27,146 | 54,178 | 70,231 |
| `review-plain` | after | 110,616 | 15,731 | 31,599 | 40,964 |
| `review-all` | before | 189,625 | 27,146 | 54,178 | 70,231 |
| `review-all` | after | 202,947 | 29,259 | 57,976 | 75,158 |
| `deep-plain` | before | 274,159 | 39,278 | 78,330 | 101,539 |
| `deep-plain` | after | 173,982 | 24,761 | 49,702 | 64,429 |
| `deep-all` | before | 274,159 | 39,278 | 78,330 | 101,539 |
| `deep-all` | after | 266,313 | 38,289 | 76,079 | 98,623 |
| `finalize` | before | 189,625 | 27,146 | 54,178 | 70,231 |
| `finalize` | after | 64,015 | 9,165 | 18,287 | 23,707 |
| `fix-loop` | before | 189,625 | 27,146 | 54,178 | 70,231 |
| `fix-loop` | after | 120,995 | 17,274 | 34,564 | 44,808 |

**Table B — measured tokens and change**

| mode path | measured (harness delta), before | measured, after | Δ% | Δ% basis |
|---|---|---|---|---|
| `review-plain` | 79,954 | not re-measured this session | −41.67% | 2.7 proxy |
| `review-all` | 79,954 | not re-measured this session | +7.02% | 2.7 proxy |
| `deep-plain` | 115,347 | not re-measured this session | −36.55% | 2.7 proxy |
| `deep-all` | 115,347 | not re-measured this session | −2.87% | 2.7 proxy |
| `finalize` | 79,954 | not re-measured this session | −66.24% | 2.7 proxy |
| `fix-loop` | 79,954 | not re-measured this session | −36.20% | 2.7 proxy |

**Why there is no AFTER measurement.** The plan assumed `footprint.py --measure` would take it. At
phase end that flag is a documented no-op. It prints "`--measure` shells `claude -p` and costs
money; it is assistant-run only …" and exits 0 without shelling out (observed 2026-09-28). I did
not build a hand-rolled substitute, because an ad-hoc measurement would not be the method the BEFORE
figures used. So the AFTER measured column says so, and every Δ% is on the 2.7 proxy. The byte Δ%
agrees with it to within 0.01 points. A proxy is never shown as a measurement here.

The four `review-*`/`deep-*` AFTER rows are **upper bounds**. `MODE_PATHS` includes the first-run
file (Phase 0.7) and the GSD intent file (Phase 1.5), which a given run may skip. The deep rows also
include the Codex pair, which is read only when `codex` is not `off`.

## 3. Chars per token: three different things

- **3.5 chars/token** is the legacy proxy constant. It was never observed on this plugin.
- **2.7 chars/token** is the D-11 restated proxy. It is a planning constant, closer to what we
  observed but still an assumption.
- **2.37–2.39 bytes/token** is what the harness delta **measured** on this plugin's markdown
  (§1). Of the three, only this one is an observation.

## 4. The D-10 soft target

The target was a **soft** 40% reduction on the plain review path. The figure achieved is
**−41.67%** by bytes and by the 2.7 proxy (189,625 → 110,616 bytes; 70,231 → 40,964 proxy
tokens). That is an upper-bound AFTER row, and no AFTER measurement was taken.
The target was **not a gate**. The gates were the per-batch checks and the catch rate, and they are recorded in the PASS
artifacts, not here. **No prose was cut to reach a number.** The restructure moved prose behind lazy
reads and turned mechanical rules into scripts. The figure is whatever that produced. Had it come in
under 40%, this section would say so and nothing would have been cut to close the gap.

## 5. Where each path's change comes from

Before the phase, every mode loaded the one 189,625-byte `commands/review.md` monolith, and deep
modes also loaded `deep-review.md`. After the phase, each mode loads a small spine
(`commands/review.md` is now 16,005 bytes; `commands/deep-review.md` is 20,255), the shared contract
and bootstrap, and only the `phases/**` files its route needs.

- **`review-plain` (−41.7%)** no longer loads the seven `--all`-only files (92,331 bytes), the fix
  loop (`phases/review/50-fix-loop.md`, 10,379), finalize (`phases/shared/90-finalize.md`, 7,339),
  or any deep-review file.
- **`review-all` (+7.0%)** loads everything `review-plain` loads plus all seven `--all`-only files.
  The monolith held the `--all` prose once, together with fix-loop and finalize prose that `--all`
  now skips. The restructure also added text: spine routing tables, the shared contract and
  bootstrap, lazy-load headers in each file, and the script-invocation wiring. In total, the
  plugin's command and phase prose is now 300,036 bytes across 2 spines and 27 phase files, against
  274,159 in the two monoliths. The `--all` route reads nearly all of it, so it grew. This is
  reported, not hidden, and D-10 does not require cutting it.
- **`deep-plain` (−36.5%)** loses the **deleted "Read `commands/review.md` end-to-end"
  instruction** (`deep-review.md:35` at `7a386ed`), which made every deep run load the whole review
  monolith on top of its own. The deep spine now reads only the shared and review phase files it
  runs, plus six `phases/deep-review/` files.
- **`deep-all` (−2.9%)** gets the same end-to-end-read removal but adds the seven `--all`-only
  files, so the two roughly cancel.
- **`finalize` (−66.2%)** runs Phases 0, 0.5 and 0.6, then reads only
  `phases/shared/90-finalize.md`. It never loads triage, dispatch, scoring, render or persist.
- **`fix-loop` (−36.2%)** is the plain path plus `phases/review/50-fix-loop.md`.

## 6. The table entries are checked on real runs

A mode path "not loading" a file is more than a table entry. `tracecheck.py`'s `forbidden_reads`
check confirms it from the tool events of a real run. See
`docs/design/mode-path-validation-v2.10.md`.
