# Phase 41 — deferred items

## From 41-06

- **Phase-42 carry: agent prompts describe the retired +10 rule.** H-LANE (41-06) removed
  `CATEGORY_DOMAIN` and the Codex single-domain bridge (STEP B). Grouping is now by site only
  (same file, ±2 lines, any category), and the +10 fires only for a Codex member plus a Claude-lane
  member when the envelope's `codex.status == "joined"` (D-01). The following prompt prose still
  teaches the old same-domain rule and must be rewritten in the prompt-only wave (Phase 42). It was
  NOT edited here because agents are out of scope for a scorer plan (T-41-30):
  - `plugins/vibe-check/agents/codex-adversarial.md` ~line 73, "Cross-confirm enabler": says the
    +10 keys on category-domain overlap and fires when exactly one native domain sits at the site.
  - Every `plugins/vibe-check/agents/framework-{angular,vue,express,react-native,fastapi}.md`
    section "Which of your categories actually cross-confirm today", plus the `CATEGORY_DOMAIN`
    mentions in `framework-react.md`, `framework-electron.md` and `framework-skill.md` ("no
    `CATEGORY_DOMAIN` twin, so the +10 never fires"). Category no longer groups, and a
    Claude-Claude pair never earns +10.
  - `bugs.md`, `architecture.md` and `index.md` also mention cross-confirmation. Re-read them
    against D-01 in the same pass.
- **Orchestrator prose carry (not in 41-06's file list): `phases/deep-review/30-codex-collect.md`.**
  Line 46 still says the +10 "fires on `(file, line ±2)` + category-domain overlap (per
  `scripts/score.py`)". Lines 6 and 46 say "No Codex special-casing downstream". Since 41-04 the
  scorer does read the envelope `codex` block, and since 41-06 the +10 is Codex + Claude only.
  Line 49's `{M} cross-confirmed` count was not re-checked against site grouping. Re-check it and
  rewrite lines 6 and 46 to D-01 when the next plan touches deep-review prose (41-04 also flagged
  this).
- **Phase-43 carry: archive the raw agent envelopes per run** so replays stop depending on
  transcripts (D-07). The 41-02 harness rebuilds each envelope from the archived state plus the
  transcript. A per-run `envelope.json` would make every future replay exact.
- **Pre-Phase-43: the Codex `BashOutput` launch-gate fix is still open.** This was deferred in
  Phase 40 (`.planning/phases/40-prose-diet-restructure-for-opus-5/deferred-items.md`). The launch
  gate requires a `BashOutput` tool that the current harness does not expose. Fix it before any
  Phase-43 measurement session.

## From 41-08

- **Runbook launch line: add the model pin.** The six `final` sessions were launched with
  `--model claude-fable-5-1` added to the SPOT-CHECK runbook's launch line, because the pin is
  Fable 5 and the owner's default model had changed. Put the `--model` flag into the Phase-43
  runbook's launch line so the pin does not depend on the owner's default.
- **Context pressure.** Every `final` session ran near 96–100% of the 200k context window. All six
  finished, but Phase 43 runs the full set ×3; check headroom (or a larger-context launch) before
  those sessions, and note it in the fingerprint block.
- **Codex skipped in should-quiet-3 runs 2 and 3** (`codex.status: skipped`, reason
  `unavailable`). Recorded, not voided (D-13). Same cause family as the open `BashOutput`
  launch-gate item below.
- **Voided attempt handling.** should-quiet-3 run 3's first attempt was voided before any review
  ran (Fable usage credits exhausted). The runbook has no explicit "voided before review" step;
  the empty auto-memory evidence folder was renamed by hand
  (`roonseek-written-before-sq3-run-3-voided-attempt`). Add a voided-attempt step to the Phase-43
  runbook.
- **`state_shape` root key (fixed in 41-08, ledger 009).** `45-persist.md` never told the model to
  create the root `medium_acknowledgments` key on a new state file. Fixed in this plan with a
  prose-lock test. The immutable `batch4` snapshot still carries the old prose; Phase 43 must run
  on a snapshot built after the fix, and its after-run `state_shape` check should then pass on
  fresh-state runs.
- **Standing carries (unchanged, restated):** Phase-42 agent prose for the retired +10 rule and
  `30-codex-collect.md` (see From 41-06); Phase-43 raw-envelope archiving per run; the Codex
  `BashOutput` launch-gate fix before any Phase-43 measurement session.
