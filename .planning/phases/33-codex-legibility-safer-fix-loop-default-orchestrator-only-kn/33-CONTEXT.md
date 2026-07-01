# Phase 33: Codex legibility + safer fix-loop default (orchestrator-only knobs) - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Three orchestrator-enforced, **no-scoring-math** knobs that make Codex behavior legible
and the fix loop's default safer:

- **LEGIBLE-01** — every run prints exactly one legible line stating what Codex did
  (joined / skipped-with-reason / off-via-config); default behavior stays `auto`.
- **LEGIBLE-02** — a `--codex` flag and a `[noise] codex` key (`off`/`auto`/`on`) control
  Codex invocation.
- **LEGIBLE-03** — the fix loop no longer nudges the apply-all option with "(Recommended)".

**Fixed scope anchor (from REQUIREMENTS.md / milestone theme):** prose + `config.py` only.
The `score.py` scoring formula, banding math, and `GOLDEN_DIGEST` are UNTOUCHED this phase
(Codex dispatch is an orchestrator concern, not a scoring concern — see D-04). Codex is a
**deep-review-only** surface; `/review` never runs Codex, so all Codex work lands in
`deep-review.md` (+ `config.py` for the validated knob). No new capability is added — this
tunes and surfaces existing Codex dispatch and existing fix-loop menus.
</domain>

<decisions>
## Implementation Decisions

### LEGIBLE-03 — which "(Recommended)" to strip (D-05)
- **D-05:** The apply-all option (`review.md` **Step A**, option 1 — "Apply all findings")
  **already carries NO "(Recommended)" label**; Step A is already documented as "a neutral
  menu with no preferred default; the user picks deliberately." So LEGIBLE-03's literal
  target is **already satisfied** — the planner MUST verify this and NOT invent a label to
  remove.
- **D-06:** The ONLY remaining "(Recommended)" in the fix loop is on **Step C** option 1
  ("Rerun review on the new diff **(Recommended if any fixes were applied)**",
  `review.md` ~line 1058). **Leave it as-is** — it is safety-POSITIVE guidance (re-review to
  confirm fixes are clean / catch regressions), not a risky auto-apply nudge, so it does not
  conflict with LEGIBLE-01's intent (don't push the user toward unsafe auto-apply).
- **D-07:** Add a **one-line guard comment** at Step A in `review.md` (e.g.
  `<!-- LEGIBLE-03: Step A is a neutral menu — do NOT add "(Recommended)" to any apply option -->`)
  so a future edit cannot silently re-introduce the nudge this requirement forbids. This is
  the phase's concrete LEGIBLE-03 change (a regression guard on an already-satisfied invariant),
  since there is nothing to delete.

### off / auto / on semantics (D-08)
- **D-08:** Three modes, precise meanings — the load-bearing decision is that **`on` NEVER
  overrides Codex's correctness (fail-closed) skips**:
  - **`off`** — never attempt Codex. Skip even the `setup --json` probe/kickoff; print the
    off-via-config outcome line (D-11). Cheapest path — no Codex work at all.
  - **`auto`** (DEFAULT — behavior UNCHANGED from today) — run Codex when it is available
    (installed + authenticated + `timeout`/`gtimeout` present) AND the mode's Phase-0 diff is
    Codex-representable; otherwise skip-and-note. This is exactly the current Phase 2c logic.
  - **`on`** — the SAME dispatch DECISION as `auto` (run iff available AND representable), but
    **any skip is surfaced as a PROMINENT notice** rather than a quiet note — semantics:
    "I expected Codex; if it didn't run, tell me clearly why." `on` behaves like auto for
    dispatch; the difference is purely legibility/prominence of the outcome line (D-11).
- **D-09 — WHY `on` must not force a launch:** two distinct skip classes exist and `on` treats
  them differently ONLY in prominence, never by forcing a run:
  - **Availability skips** (not-installed / unauthenticated / no-timeout-binary) — Codex
    *cannot* run here.
  - **Correctness / fail-closed skips** (diff not Codex-representable — `--all`
    whole-repo `whole-repo-non-representable`; GSD phase with an uncommitted tail
    `phase-diff-has-uncommitted-tail`; non-ancestor range; PR head mismatch) — Codex *could*
    launch but would review the **WRONG/PARTIAL diff and silently miss real defects**. This is
    the SAFE-01 guarantee from Phase v2.2/earlier: a Codex limitation degrades to a clean skip,
    never a silent wrong review. **`on` MUST preserve every correctness skip unchanged** —
    forcing Codex onto a non-representable diff is explicitly forbidden. So `on` ≠ "bypass
    safety"; it only makes the skip louder.
- **D-10 — `--codex` flag surface:** `--codex` accepts the SAME three values `off|auto|on`
  (not a bare on/off toggle), matching the `[noise] codex` key and the richer `[noise]` schema.
  Precedence per the Phase-30 chain: **flag (`--codex`) > toml (`[noise] codex`) > default
  (`auto`)**, resolved through `config.py`'s existing `_apply_flags` overlay (the precedence
  slot `config.py:253` already reserves for `--codex`).

### LEGIBLE-01 — the always-on outcome line (D-11)
- **D-11:** Print **exactly one OUTCOME line per run**, at **Phase 3 (post-collection)** in
  `deep-review.md`, because the true outcome is only known after collection (a launch can
  still time out). Three forms, and the line is UNCONDITIONAL (fires on every deep-review run,
  including off and skip):
  - **joined:** `✓ Codex joined — {N} findings ({M} cross-confirmed)` (N = Codex findings that
    survived Phase-3 filtering; M = those that got the +10 cross-confirm).
  - **skipped-with-reason:** `⊘ Codex skipped: <reason slug>` — REUSE the existing reason slugs
    already defined in Phase 2c (`not-installed`, `unauthenticated`, `no-timeout-binary`,
    `timeout`, `whole-repo-non-representable`, `phase-diff-has-uncommitted-tail`,
    `range-not-identical`, `head-not-at-target`). Do NOT invent new slugs.
  - **off-via-config:** `⊘ Codex off via [noise] codex=off` (or `via --codex off` when the flag
    was the deciding layer — planner's call on whether to name the deciding source).
- **D-12 — `on`-mode prominence:** under `codex=on`, the skip/off forms of the outcome line
  render in the MORE PROMINENT notice style (D-08 `on` semantics) — e.g. a `⚠`-weighted line
  instead of the quiet `⊘`. Under `auto`/`off` they render in the normal quiet style. Exact
  glyph/format is the planner's discretion; the REQUIREMENT is that `on` makes a non-run
  visibly louder.
- **D-13 — kickoff line unchanged:** the existing Phase 2c kickoff *progress* line
  (`▶ Running Codex adversarial review in parallel …`) STAYS, and fires ONLY when Codex
  actually launches. It is a progress line, distinct from the D-11 outcome line; do NOT merge
  them and do NOT make the kickoff line unconditional (that would print "running" on a run
  that never launches). Exactly ONE new always-on line is added: the D-11 outcome line.

### config.py vs pure-prose — where the codex knob is validated (D-14)
- **D-14:** `codex` becomes a **`config.py`-validated knob**, NOT untested markdown parsing.
  - Add `codex` to `config.py`'s knob roster (`_DEFAULT_VALUES`, a `_validate_codex`
    validator, and the `_apply_flags` validators map) with default `"auto"`. A value not in
    `{off, auto, on}` (wrong type, unknown string) degrades to `"auto"` + a config-health
    warning line, EXACTLY like every other knob's fail-safe (`config: codex invalid
    (<reason>) — using default`).
  - Resolution flows through the same `read_config(... flags=...)` → `_apply_flags` precedence
    machinery `disabled`/`top_model`/`min_confidence`/`idiom_floor` already use. The
    orchestrator carries the resolved value forward as `$CONFIG_CODEX` at `review.md` Phase 0.6
    (unconditional config read) and `deep-review.md` CONSUMES it in Phase 2c (dispatch
    decision) + Phase 3 (outcome line), parallel to how `$CONFIG_DISABLED`/`$CONFIG_TOP_MODEL`
    are consumed.
  - **"orchestrator/prose only" is honored** because this adds NO `score.py` / scoring-math /
    envelope-key change — `codex` is an ORCHESTRATOR-only knob (like `disabled`/`top_model`),
    never entering the `score.py` stdin envelope. This matches Phase 30 **D-03**: the per-key
    fail-safe is the load-bearing milestone invariant, so validators live in the unit-tested
    `config.py` helper, not in untested markdown.

### Claude's Discretion
- Exact glyphs/format of the outcome line and the `on`-prominence styling (D-11/D-12), within
  the stated shapes.
- Exact wording of the Step A guard comment (D-07).
- Whether the off-via-config line names the deciding source (toml vs flag) when both are set
  (D-11) — nice-to-have, not required.
- Placement details of `$CONFIG_CODEX` carry-forward, following the established
  `$CONFIG_DISABLED`/`$CONFIG_TOP_MODEL` carry pattern.
</decisions>

<specifics>
## Specific Ideas

- The `on` mode's honest framing came directly from the owner: it must NOT claim to force a
  wrong-diff review — "on == auto + louder" is the agreed semantics, never "on == bypass the
  safety skips."
- Reuse-not-reinvent is explicit: the outcome line reuses the EXISTING Phase-2c reason slugs;
  the flag reuses the EXISTING `config.py:253` precedence slot; the validator mirrors the
  EXISTING `_validate_top_model` shape.
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & milestone scope
- `.planning/REQUIREMENTS.md` §Legibility — LEGIBLE-01/02/03 exact text; §Out of Scope
  ("Making Codex default-off" is EXCLUDED — default stays `auto`; scoring-formula rewrite
  EXCLUDED).

### Carried-forward config-surface decisions (Phase 30 — the config machinery this phase extends)
- `.planning/phases/30-config-surface-foundation/30-CONTEXT.md` — **D-03** (validators live in
  the tested `config.py` helper, not markdown prose), **D-02/D-04** (per-key fail-safe →
  config-health warning line), and the flag > toml > default precedence chain (CONFIG-02).

### Edit sites (read before writing tasks)
- `plugins/vibe-check/scripts/config.py` — knob roster: `_DEFAULT_VALUES` (line ~52),
  `_apply_flags` validators map + the reserved `--codex` slot (line ~253); mirror
  `_validate_top_model` (line ~177) for `_validate_codex`.
- `plugins/vibe-check/commands/deep-review.md` — **Phase 2c** (Codex kickoff: probe + skip
  gate + reason slugs + kickoff line, lines ~218–287); **Phase 3** (Codex collection / join,
  lines ~301+ — the outcome line lands here); and the deep Selection-table carry-forward prose
  (line ~83, where `$CONFIG_*` vars are consumed) as the model for `$CONFIG_CODEX`.
- `plugins/vibe-check/commands/review.md` — **Step A** fix-loop menu (lines ~994–1003, add
  guard comment) and **Step C** menu (line ~1058, the "(Recommended)" to LEAVE).
- `plugins/vibe-check/scripts/test_config.py` — add `codex` validator/precedence/fail-safe
  cases here (the phase's test surface; `test_verify_cmd` = `pytest -q` in
  `plugins/vibe-check/scripts`).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config.py` `_apply_flags` (line ~245) + the reserved `--codex` precedence slot (line ~253)
  — the exact mechanism `codex` plugs into; no new precedence code needed.
- `config.py` `_validate_top_model` (line ~177) — closest validator analog (a small
  fixed-enum string knob); `_validate_codex` is the same shape over `{off, auto, on}`.
- `deep-review.md` Phase 2c `CODEX_SKIPPED` authoritative skip flag + the full reason-slug
  vocabulary — the outcome line and the `off` short-circuit reuse these, not new machinery.

### Established Patterns
- Orchestrator-only knobs (`disabled`, `top_model`) are validated in `config.py` yet never
  touch `score.py` — `codex` follows this exact split (validated knob, orchestrator-consumed,
  zero envelope impact).
- "Never silently drop a misconfiguration" → every bad knob value emits a config-health
  warning line (Phase 30 D-04). `codex` inherits this.
- Codex is deep-review-only; `/review` has no Codex path — so LEGIBLE-01/02 changes are
  confined to `deep-review.md` (+ `config.py`), and `review.md` only gets the LEGIBLE-03
  guard comment.

### Integration Points
- `review.md` Phase 0.6 (unconditional config read) resolves `$CONFIG_CODEX`; `deep-review.md`
  Phase 2c consumes it for the dispatch decision and Phase 3 for the outcome line — same
  carry-forward path as `$CONFIG_DISABLED`/`$CONFIG_TOP_MODEL`.
</code_context>

<deferred>
## Deferred Ideas

- **`on`-forces-availability-hard-fail** (the rejected Area-2 option 2): making `codex=on`
  HALT the run when Codex is unavailable for availability reasons. Rejected for this phase —
  adds a new failure/halt path; `on == auto + louder` is the chosen, lower-risk semantics.
  Note for a future milestone if a hard "require Codex" guarantee is ever wanted.
- **Temp-worktree checkout to make non-representable diffs Codex-reviewable** (already a
  DEFERRED note in `deep-review.md` Phase 2c) — would let `on` genuinely run on `--all` /
  uncommitted-tail / non-ancestor ranges. Out of scope; correctness skips stand this phase.
- **Flipping the Codex default to `off`** — explicitly OUT OF SCOPE per REQUIREMENTS.md; the
  default stays `auto`.

---

*Phase: 33-codex-legibility-safer-fix-loop-default-orchestrator-only-kn*
*Context gathered: 2026-07-01*
