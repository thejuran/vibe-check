# vibe-check — Design Hypotheses (falsifiable form, for the Fable design review)

> **Status:** Opus, 2026-07-01. vibe-check already has committed per-milestone design-rationale
> docs (`docs/superpowers/specs/*-design.md`) — this doc does NOT replace them. It **extracts
> the design's load-bearing choices as falsifiable hypotheses** so a second model (Fable) can
> attack them in a form the project's efficacy method can adjudicate, and so challenges to the
> in-flight v2.8 LOCKED decisions route to a parking lot instead of derailing the milestone.
>
> Companion to `fable-review-leverage-map.md` (which explains *why* these are the targets) and
> `fable-code-review-prompt.md` (the separate correctness pass).

## Copy-paste prompt (Pass B2 — run in a FRESH Fable session at the repo root)

```
You are Fable, a second frontier model, doing an adversarial DESIGN review of vibe-check — a
code-review tool the owner relies on as his SOLE reviewer (his other automated review is
disabled). You are the independent second-model lens: model diversity is the whole reason
you're here — a different model catches what the author's model can't. This is NOT a bug hunt
(that's a separate pass); it's about whether the DESIGN is sound and earns the trust placed
in it.

## Read first (repo root: /Users/julianamacbook/turingmind-code-review)
- docs/design/design-hypotheses.md        ← YOUR PRIMARY TARGET. Falsifiable hypotheses, an
  owner-profile section, and the §A/§B split that governs your output. Read it fully.
- docs/design/fable-review-leverage-map.md ← why these are the targets (context).
- docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md ← the v2.8 committed
  spec; §5 states the LOCKED "scoring-formula-untouched" decision.
- plugins/vibe-check/templates/scoring.md and plugins/vibe-check/docs/architecture.md ← the
  scoring rationale.
- plugins/vibe-check/docs/efficacy/ANSWER-KEY.md ← the ground-truth test set you will also
  attack (its S-item / B-item classification).

## Who the owner is
A product manager who understands software deeply — architecture, data flow, tradeoffs — but
cannot verify a diff by reading it. vibe-check is his sole reviewer, so a wrong verdict is one
he cannot catch. Two properties are therefore non-negotiable: (1) false negatives on real bugs
are the worst class; (2) noise is nearly as costly, because a PM who can't adjudicate findings
can't triage a flood. A "the owner can just judge X himself" challenge is admissible only if X
is architecture/behavior/tradeoff-level, not if it needs reading an implementation.

## The remit (binding)
You MAY challenge anything in design-hypotheses.md, including the v2.8 LOCKED decision that the
scoring formula is untouched. Every objection must resolve to ONE of:
  (a) a counter-hypothesis + the specific fixture/planted-item/metric that would prove it
      (routes to vibe-check's efficacy method);
  (b) "the stated constraint is wrong because ___" (returns to the owner as a product call);
  (c) concede.
A bare "I'd design it differently" is NOT admissible.

Sort EVERY finding into one of two buckets (this is the owner's explicit instruction):
  §A — within the lock: challenges that do NOT require re-weighting the scoring formula or
       severity weights. Actionable now; can inform the remaining v2.8 phases.
  §B — challenges the lock itself: any argument that agent_confidence derivation or the
       severity weights (0/-3/-8/-20) should change. Parked for post-v2.8; nothing suppressed,
       the owner triages what graduates.
The hypotheses in design-hypotheses.md are already pre-tagged §A (H-CORE, H-DUP1, H-DUP2,
H-LANE, H-KNOB, H-COUPLE, H-CODEX-TRUST) and §B (B-SEV, B-XCONF, B-PROX, B-REWEIGHT) — respect
that tagging, and put any NEW finding in the right bucket.

## Deliverables
1. Go through the §A hypotheses one by one. For each you contest: hypothesis ID, challenge
   type (a/b/c), and the full counter-hypothesis+fixture / mis-stated-constraint / concession.
   Prioritize H-CORE (the central "agents over-report, orchestrator filters" bet), H-DUP1/H-DUP2
   (do overlapping agents earn their place?), and H-KNOB (do the v2.8 noise knobs suppress real
   bugs?).
2. Go through the §B hypotheses the same way — everything lands in the parked bucket.
3. Attack ANSWER-KEY.md's S/B classification directly. If you'd class a B-item (bait, meant to
   stay silent) as a real bug, or an S-item as one that shouldn't fire, say so — that's either
   a vibe-check blind spot or an answer-key flaw, a finding either way.
4. Flag that you're available as the variant-D reviewer for the product-quality harness: given
   real diffs, your independent findings vs vibe-check's are the cross-model data point.

## Output format
Group by §A then §B. Within each: hypothesis ID | verdict (challenged/conceded) | type (a/b/c) |
the falsifiable counter-hypothesis + the fixture or metric that would settle it. Do NOT edit
code or the design docs. Report only.
```

## The remit (binding — mirrors the julian-orchestrator second-model contract)

Fable may challenge ANYTHING here, including decisions the v2.8 spec marks LOCKED. But per the
owner's decision (2026-07-01), every finding is sorted into one of two buckets:

- **§A — within the lock (actionable now):** challenges that do NOT require re-weighting the
  scoring formula or severity weights. These can inform the remaining v2.8 phases.
- **§B — challenges the lock itself (parked):** challenges to `scoring-formula-untouched` —
  arguments that `agent_confidence` derivation or the severity weights `0/−3/−8/−20` should
  change. Nothing is suppressed; these are captured in a separate section for post-v2.8
  consideration. The owner decides what graduates from §B to actionable.

Every objection must resolve to ONE of: (a) a counter-hypothesis + the falsifying test/metric
(routes to the efficacy method — see below); (b) "the stated constraint is wrong because ___"
(returns to the owner as a product call); (c) concede. A bare "I'd design it differently" is
not admissible.

## The efficacy method these hypotheses route to (important context)

vibe-check's efficacy is measured by planted-fixture ground-truth sets (`ANSWER-KEY.md`
style: S-items that should fire, B-items = bait that must stay silent, N=3 stability). It has
a **self-documented gap: no aggregate catch-rate / false-positive-rate number is ever
computed** (`RESULTS.md:64`). A falsifiable challenge here is strongest when it names the
planted item (or proposes one) that would prove it. The product-quality harness (Pass B3)
extends the answer-key with the owner's real past diffs to give these hypotheses a broader
ground truth.

---

## The owner profile (read first — it sets which challenges are admissible)

The owner is a product manager who understands software deeply — architecture, data flow,
tradeoffs — but **cannot verify a diff by reading it.** vibe-check is his **sole code
reviewer** (GSD's built-in review is disabled in his milestone loop). So a wrong verdict is
one he cannot catch. This makes two design properties non-negotiable, and any challenge must
respect them:
- **False negatives on real bugs are the worst class** — a missed bug ships unnoticed.
- **But noise is nearly as costly** — a PM who can't adjudicate findings can't triage a flood;
  he must be able to trust that what surfaces is real. This is *why* the "quieter reviews"
  theme exists.
A (b)-type "the owner can just judge X himself" challenge is admissible only if X is
architecture/behavior/tradeoff-level, NOT if it needs reading an implementation.

---

## §A hypotheses — within the lock (attack freely, actionable now)

**H-CORE — Agents over-report; the orchestrator filters. (The central bet.)**
Every detection agent is instructed "coverage, not filtering — report everything, don't
self-filter"; no agent references `false-positive-rules.md`. ALL noise suppression is
`score.py`-side, backed by the ≥80 (`/review`) / ≥70 (`/deep-review`) thresholds.
- **Claim:** centralizing filtering in the scorer produces better signal:noise than letting
  agents self-filter, because the scorer has cross-agent facts (cross-confirm, in_diff
  verification) an individual agent lacks.
- **Refutable by:** a fixture where the over-report-then-filter path lets a B-item (bait)
  surface ≥70 that an agent-side filter would have caught — i.e. the central bet produces
  noise the thresholds miss. The `ANSWER-KEY` B1–B5 are exactly this instrument; propose new
  baits that stress it.
- **This is the highest-value hypothesis** — it's the design's spine and the thing the
  "quieter reviews" milestone is implicitly betting on.

**H-DUP1 — language-typescript and framework-react earn their overlap.**
Both check React hook rules; they're declared cross-confirm twins (`hooks`↔`react-hook` →
`style` domain), so the same missing-dep-array is surfaced by both, earning +10.
- **Claim:** the redundancy is worth it — two independent flags on a real hook bug raise
  confidence; the +10 is the intended reward.
- **Refutable by:** a fixture showing the twin produces double-reported NOISE (both flag a
  non-bug at the same site, cross-confirm to +10, and surface a false positive that neither
  alone would have surfaced) more often than it rescues a real catch. Or: language-typescript's
  hook-checking never independently catches anything framework-react misses → it's dead weight.

**H-DUP2 — architecture and impact are distinct enough to both run.**
Two opus, deep-only, cross-file agents with adjacent scope (coupling/duplication vs
blast-radius/breaking-API), NOT dedup-linked in `CATEGORY_DOMAIN` — so they can double-report
the same structural concern with no merge credit.
- **Claim:** they cover genuinely different failure modes and the lack of a dedup link is
  correct (their findings aren't the same defect).
- **Refutable by:** a fixture where both fire on one structural change (e.g. an import-
  signature change) producing two findings for one concern, un-merged, inflating the count the
  owner sees. Two of the most expensive agents (opus) — if they overlap, it's costly noise.

**H-LANE — the react-native lane boundary holds.**
`framework-react-native` is instructed (prose, not mechanism) not to re-emit generic
hook/key/dep-array/rendering/a11y — those stay with `framework-react` on dual-emit diffs.
- **Claim:** instruction-enforcement is sufficient; the agent obeys its lane.
- **Refutable by:** an RN fixture where react-native re-emits a generic React finding
  framework-react also emits → double-report, because nothing mechanical prevents it.

**H-KNOB — the v2.8 noise knobs actually reduce noise without hiding real bugs.**
`min_confidence`, `idiom_floor` (default `medium`), `vibe-ignore` marker.
- **Claim (from the spec's definition-of-done):** these filter noise while nothing real
  silently vanishes (dropped counts stay in the honesty summary; bare `vibe-ignore` → low
  finding for audit trail).
- **Refutable by:** a fixture where a knob at a plausible setting (e.g. `min_confidence=60`)
  drops a real S-item — i.e. the noise control also suppresses signal. Or where `idiom_floor`
  caps a category that sometimes carries a real blocking bug.

**H-COUPLE — config changes thresholds/filtering WITHOUT touching the scoring math.**
The v2.8 LOCK. `thresholds` parameterize `band_for()`; `min_confidence` filters pre-scoring;
neither is a parameter of `compute_score`.
- **Claim:** the boundary is clean — zero-config output is byte-identical (GOLDEN_DIGEST
  unmoved), config only relabels/filters.
- **Refutable by:** any path where a config value reaches `compute_score` and changes a
  score (not just a band label or a set membership). This is a within-lock correctness claim
  Fable can verify by tracing the envelope.

**H-CODEX-TRUST — the codex-adversarial translation safely admits untrusted output.**
The one place external (GPT-5-codex) output enters the trusted pipeline; guarded by title
sanitization, realpath path-containment, 300-char anti-spoof caps.
- **Claim:** the sanitization is sufficient — a malicious/garbled codex finding can't spoof a
  report, escape its file, or inject via title.
- **Refutable by:** a crafted codex-output fixture that defeats a guard. (This overlaps the
  code-review pass but belongs here too because it's a *design* question: is translating
  adversarial output into the trusted schema the right architecture at all, vs keeping it in a
  separate quarantined channel?)

### Orchestration-layer hypotheses (O-series — added 2026-07-01 from external feedback)

All within the lock (none touch the scoring formula). These target the prose/bash layer the
original four-way read scoped out. Each is a NARROW-generation move in the owner's axiom:
"hope the model ran the check" → "the check is code." (The external review that surfaced these
had stale facts about agent count/file sizes/commit count — see the leverage map's stale-note;
only the items below survived verification against the real v2.7 tree.)

**O-EXTRACT (was O1) — Deterministic prose should be tested code, per-block by risk-vs-coupling.**
A full sweep (see `prose-to-code-inventory.md`) found ~30 deterministic prose/bash blocks that
consolidate into **three extraction families**, plus a KEEP list where extraction costs more
than it saves. This is NOT "scriptify everything" — it's a per-block judgment Fable stress-tests.
- **Family 1 — path validation** (regex allowlist + `..`/pathspec-magic reject + realpath-
  containment), **5 files / ≥6 copies already diverging**. Security boundary; tool auto-commits
  → a containment miss is a write-outside-repo. **Highest.**
- **Family 2 — chunk-packer + risk math** (`review.md:237-306`), the purest input→output logic
  in the repo, feeds three consumers via `$CHUNK_PLAN`. Free win, low coupling.
- **Family 3 — codex output sanitization** (bidi/zero-width/control strip + 300-char cap +
  field translation), Unicode codepoint list re-typed across 2 files → highest-consequence
  copy-paste (untrusted input into an autonomous committer).
- **Claim (the design position to attack):** the current prose-bash is correct on every run,
  AND the KEEP-list blocks (churn one-pass, `wc` sizing, cost brackets, the plugin resolver)
  are right to stay prose because extraction breaks `score.py` purity / adds serialization /
  is chicken-and-egg.
- **Refutable by:** (per family) exhibit an input where two of the duplicated copies behave
  differently (proves drift is live) OR where the model plausibly mis-transcribes the prose and
  a path escapes / a chunk mis-packs / a codex output mis-sanitizes. For the KEEP list: show a
  block we kept that's actually a latent bug, or an extract we recommended that has hidden
  coupling. **Highest-value new item.**

**O3 — The fix loop needs a post-apply verification gate.**
`fix.md:21` self-checks only by re-reading the changed region; no typecheck/lint/test runs;
`--no-verify` is banned so pre-commit hooks are the sole backstop (repo-dependent).
- **Claim:** re-reading the region + pre-commit hooks are sufficient soundness for an
  autonomous committer.
- **Refutable by:** a fixture where an LLM-applied fix is syntactically plausible (passes the
  re-read) but introduces a type error or breaks a test that a typecheck/test run would catch.
  Trivially constructible → likely a concede-to-the-feedback. **Second-highest new item.**

**O5d — `allowed-tools` under-declares the interpreters actually run.**
Declared: `git`, `gh`, `node`. Invoked in prose: `python3`, `realpath`, `wc`, `sort`, `grep`,
`xargs`, `uniq`, `sed` — none declared, prose says "do NOT add them."
- **Claim:** the compound-Bash convention makes declaration unnecessary/undesirable.
- **Refutable by:** a permission-mode or autonomous run where an undeclared interpreter
  triggers a prompt or a denied call — i.e. the stated permission surface doesn't match what
  runs. (b)-type: "the constraint is wrong — declare honestly or document the convention."

**O-CI / O-CHANGELOG (lower priority):** no CI re-runs the `ANSWER-KEY`/`RESULTS` eval corpus
(prompt regressions go uncaught); no `CHANGELOG` at v2.7.0/332 commits. Both already in the
project backlog; note them, don't over-invest Fable effort here.

---

## §B hypotheses — challenge the lock itself (parked for post-v2.8)

These question `scoring-formula-untouched` directly. Capture Fable's challenge; the owner
decides if/when any graduate. Each must still be falsifiable (counter-hypothesis + test).

**B-SEV — the severity weights `0/−3/−8/−20` are miscalibrated.**
Self-consciously re-tuned once already (from `−5/−15/−25`, because the steeper spread
suppressed real mediums — `scoring.md:33`). That history means the "right" spread is empirical,
not settled.
- **Refutable/provable by:** a fixture set where a *different* spread changes the S/B outcome
  — i.e. the current weights let a real medium get filtered, or let a low-severity nitpick
  surface, that a better spread would fix.

**B-XCONF — the flat, once `+10` cross-confirmation bonus is wrong.**
Fires once per group regardless of 2 vs 3+ agents; magnitude is a guess.
- **Refutable by:** a fixture where 3-agent confirmation should outrank 2-agent (or where +10
  over-rewards a coincidental co-location) and the flat bonus mis-bands it.

**B-PROX — the `±2` proximity window is the wrong radius.**
One magic number governs BOTH cross-confirm grouping AND silenced-marker detection — coupling
two unrelated behaviors to one constant.
- **Refutable by:** a case where the right window for silencing (tight) differs from the right
  window for cross-confirm (looser), so one radius can't serve both.

**B-REWEIGHT — `agent_confidence` should be re-derived, not taken as agent input.**
The formula trusts each agent's self-reported confidence (coerced) as the base. The lock
forbids re-deriving it.
- **Refutable by:** evidence that agent self-confidence is poorly calibrated (a high-confidence
  false positive class, or a low-confidence real-bug class) that an orchestrator-side
  re-derivation would fix. This is the deepest challenge — it questions the base of the whole
  formula.

---

## How Fable uses this doc (deliverables)

1. Go through §A hypothesis-by-hypothesis: for each contested, output challenge type (a/b/c)
   + the full counter-hypothesis+fixture / mis-stated-constraint / concession. Prioritize
   H-CORE, H-DUP1/2, H-KNOB.
2. Go through §B the same way, but everything lands in the parked bucket — the owner triages.
3. Attack `ANSWER-KEY.md` itself: is the S/B classification correct? If you'd class a B-item
   (bait) as a real bug or vice-versa, that's either a vibe-check blind spot or an answer-key
   flaw — a finding either way.
4. You are also the variant-D reviewer for the product-quality harness (Pass B3): given real
   diffs, your independent findings vs vibe-check's are the cross-model data point.

## Cross-references
- Leverage map: `fable-review-leverage-map.md`
- Code-review pass: `fable-code-review-prompt.md`
- v2.8 committed spec (the LOCK source): `docs/superpowers/specs/2026-06-30-tunable-quieter-reviews-design.md`
- Scoring rationale: `plugins/vibe-check/templates/scoring.md`, `plugins/vibe-check/docs/architecture.md`
- Ground truth: `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md`
