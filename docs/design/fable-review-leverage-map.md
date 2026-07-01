# vibe-check — Fable Review Leverage Map (Phase A)

> **Status:** Opus, 2026-07-01. This map aims a second-model (Fable) review at the
> highest-leverage targets in vibe-check, so Fable's effort lands on the
> **high-reliance / under-verified** quadrant instead of spreading uniformly over a tool
> that is already one of the most-dogfooded things in the codebase.
>
> Built from a four-way parallel read of the v2.7 stable surface: scoring engine
> (`score.py`), the 22-agent fleet, the config surface (`config.py`), and the efficacy
> docs + v2.8 roadmap. Findings below cite `file:line`.

## The reliance premise (why this review exists)

The owner relies on vibe-check heavily — it is the **sole code reviewer** in the milestone
loop (GSD's built-in review is disabled), and the owner is a PM who cannot verify a diff by
reading it. So a wrong verdict from vibe-check is a wrong verdict the owner *cannot catch*.
That makes the review's job specific: not "find bugs in vibe-check" (its own dogfood + codex
stack already does that well), but **"where could vibe-check be silently wrong in a way its
own verification wouldn't catch, and does its design actually earn the trust placed in it?"**

## The core finding: vibe-check is heavily verified, but unevenly

| Subsystem | Existing verification | Reliance | Leverage quadrant |
|---|---|---|---|
| `score.py` scoring engine | **Very high** — T1–T21 malformed matrix, AST import-ban, golden digest, permutation order-tests, exhaustive band-boundary tests | High (every verdict flows through it) | **Low code-review leverage / HIGH design-review leverage** |
| `config.py` config surface | **High** — 33 tests, never-raise contract, DoS/symlink/unicode guards | Rising (v2.8 makes it the spine) | **Low-medium** — a few real test gaps + one cross-file drift risk |
| 22-agent fleet | **Medium** — dogfood catches regressions in changed agents; rubrics unverified | High (agents produce the raw signal) | **HIGH design-review leverage** — "does each agent earn its place?" |
| Efficacy method | **Named gap** — no aggregate catch/FP rate ever computed | High (it's how "is it good?" is answered) | **HIGHEST product-quality leverage** — the hole to fill |

**The headline:** the *code* is well-verified; the **design choices** (magic numbers, the
over-report-then-filter bet, agent overlap) and the **product-quality measurement** are the
under-verified surfaces. So Fable's weight goes there, not on hunting `score.py` bugs.

---

## Target set A — Code correctness (narrow; one real candidate)

`score.py` is hardened enough that the four-way read found **smells, not confirmed bugs**.
The one worth Fable confirming as variant-D:

- **A1 — Tie-break order-dependence (`score.py:904-906`).** The comment claims "keep first
  on ties," but among same-score members of a cross-confirm group, the *representative*
  chosen (whose title/file/current_code/stable_hash get emitted, and whose dismissal key
  persists) is **input-order-dependent**. Grouping is order-independent and tested; the
  representative choice is **not tested**. Real, latent, and exactly the kind of thing a
  fresh model confirms or refutes. **Highest code-review priority.**

Lower-priority smells (Fable can sweep, but low expected yield):
- `_is_low_entropy` empty-string docstring contradicts the `len < 4` clause (`score.py:212`).
- `persisted` uses `id(member)` identity detection (`score.py:1055`) — works today, latent
  trap if a future copy is introduced; `status=="persisted"` fallback covers it.
- `min_confidence` drop labeled `"sub-threshold"` even when the drop was intent-doc-driven
  (`score.py:1064-1068`) — reporting-accuracy, not a crash.
- `SILENCED_MARKERS` case-sensitive substring (`score.py:40`) — an `ESLint-disable` escapes
  the −50.
- **Cross-file constant duplication:** `config.py:72` `_MEDIUM_FLOOR = 70` must stay in sync
  with `score.py:44` `THRESHOLDS["deep-review"] = 70`; linked only by a prose comment, no
  test asserts equality. **Real drift risk** — worth Fable flagging as a maintainability bug.

---

## Target set B — Design / efficacy hypotheses (rich; the main event)

Every item here is a **choice that could reasonably be different** — the falsifiable-
hypothesis surface. These become the vibe-check design-rationale attack surface (Phase B2),
routed to the efficacy method (extended per Phase B3).

**The central bet (highest-leverage hypothesis):**
- **H-CORE — Agents over-report; the orchestrator filters.** Every detection agent is told
  "coverage, not filtering — report everything, don't self-filter"; **no agent references
  `false-positive-rules.md`** — all noise suppression is `score.py`-side (bugs.md:19-21 and
  siblings). This is the single biggest design decision. Falsifiable: *does orchestrator-side
  filtering actually beat agent-side filtering, or does it generate noise the ≥80/≥70
  thresholds mostly-but-not-always catch?* The `ANSWER-KEY` B-items (bait that must stay
  silent) are the instrument that measures exactly this.

**"Does each agent earn its place?" (fleet):**
- **H-DUP1 — language-typescript vs framework-react** both check React hook rules and are
  declared twins (same defect surfaced twice by design). Does the +10 cross-confirm justify
  the redundancy, or is one agent's hook-checking dead weight?
- **H-DUP2 — architecture vs impact** — adjacent cross-file opus deep-only agents, **NOT
  dedup-linked** in `CATEGORY_DOMAIN`, so they can double-report the same structural concern
  with no merge credit. Two of the most expensive agents (opus) with the vaguest rubrics.
- **H-LANE — react-native lane boundary is instruction-enforced, not mechanical**
  (framework-react-native.md:7). Correctness depends on the agent *obeying* "don't re-emit
  generic hook/key/dep-array." Fragile — a probe target.

**Magic numbers (each a "does this value earn its place?" hypothesis) — all in `score.py`:**
- Severity weights `0/−3/−8/−20` (`:35`) — self-consciously re-tuned from `−5/−15/−25`
  because the steeper spread suppressed real mediums; the most-defended number in the system.
- Cross-confirm bonus `+10`, flat and once regardless of 2 vs 3+ agents (`:353`).
- Proximity window `±2` (`:544`) — governs **both** cross-confirm grouping **and** silenced-
  marker detection; one radius, two behaviors.
- Intent-doc thresholds `0.9 / 0.7`, strict `>` (`:295`).
- Compliance blanket `+20` keyed on the literal string `"compliance"` (`:349`).
- `CATEGORY_DOMAIN` twin map (`:392-503`) — which categories are cross-agent twins vs
  deliberately unmapped is pure editorial judgment.

**codex-adversarial translation (`deep-review.md:313-346`)** — the one place a bug is a
*security* issue, not noise: untrusted external (GPT-5-codex) output entering the trusted
pipeline. Title sanitization, path realpath-containment, 300-char anti-spoof cap. High-value
adversarial target for a second model specifically.

---

## Target set B2 — Orchestration layer (added 2026-07-01 from external feedback)

The four-way read scoped to the *Python* (`score.py`/`config.py`) and the *agents*. An external
design review surfaced a third under-verified surface our prep had missed: the **prose/bash
orchestration layer** in `commands/*.md` and `agents/fix.md`. These are verified-real against
v2.7 (the same review's factual claims about agent count and file sizes were STALE — see the
"stale feedback" note below — but its *architectural* instincts hit real gaps). Each is a
NARROW-generation move in the owner's own axiom: convert "hope the model ran the check" into
"the check is code."

- **O-EXTRACT (was O1) — Deterministic prose should be tested code, per-block.** A full sweep
  (see `prose-to-code-inventory.md`) found ~30 deterministic prose/bash blocks consolidating
  into **three extraction families** — (1) path validation [5 files/≥6 copies already diverging,
  security boundary], (2) chunk-packer + risk math [`review.md:237-306`, purest logic in the
  repo], (3) codex output sanitization [Unicode strip + caps, re-typed across 2 files] — plus a
  KEEP list where extraction breaks `score.py` purity / adds serialization / is chicken-and-egg
  (churn one-pass, `wc` sizing, cost brackets, the plugin resolver). No `scripts/guard.py` or
  packer module exists though `score.py`/`config.py` prove the pattern. **This is NOT "scriptify
  everything" — it's the per-block risk-vs-coupling judgment.** Since the tool auto-commits, the
  path-validation family is the single biggest correctness lever. **Highest-value new item.**
- **O3 — No verification pass after the fix loop.** `fix.md:21` is the ONLY self-check
  ("re-read the changed region, confirm syntactically plausible"); it never runs typecheck,
  lint, or tests. `--no-verify` is banned (`fix.md:52`) so pre-commit hooks are the ONLY
  backstop — and only if the repo has them. An LLM-applied fix can commit a fresh type error
  or break a test, unnoticed. **Hypothesis:** an optional "run the project's typecheck/test
  after fixes, surface failures, offer to revert" step closes the soundness gap inherent to
  any autonomous-commit tool. (Note: julian-orchestrator HAS this gate — BUILD/TEST-VERIFY —
  but that's the milestone wrapper; standalone vibe-check has no equivalent.)
- **O5d — allowed-tools under-declares what runs.** Declared: `git`, `gh`, `node`. Actually
  invoked in prose: `wc`×31, `python3`×15, `realpath`×13, `sort`×12, `grep`×10, `xargs`,
  `uniq`, `sed` — none declared, and the prose explicitly instructs "do NOT add them to
  allowed-tools." **Hypothesis:** either declare them honestly or document the compound-Bash
  convention, so the stated permission surface matches what runs. (Same class as
  julian-orchestrator's TOOL-01 fix.)
- **O-CI / O-CHANGELOG (lower priority, both valid):** no CI runs the eval corpus (the
  `ANSWER-KEY`/`RESULTS` sets exist but nothing re-runs them → prompt regressions go
  uncaught); no `CHANGELOG` despite 332 commits and v2.7.0. Both are in the project's own
  backlog already.

**Stale-feedback note (so these aren't confused with the reviewer's errors):** the external
review analyzed an OLDER version. Its false claims — "only 4 specialist agents" (v2.7 has 12),
"review.md ~148KB/977 lines" (actually 167KB/1068), "no eval corpus" (ANSWER-KEY exists),
"96 commits" (332) — are all stale and should NOT be actioned. Only O1/O3/O5d/O-CI/O-CHANGELOG
above survived verification against the real v2.7 tree.

---

## Target set C — Product quality (the named gap; highest owner value)

The efficacy method has a **deliberate, self-documented hole**: it produces binary pass-gates
+ per-item score tables + "high catch / low false-alarm" *prose*, but **no aggregate
catch-rate / false-positive-rate number, ever** (`RESULTS.md:64` admits it "does not measure
recall across the full surface").

**What exists to build on:**
- `ANSWER-KEY.md` — a genuine, rigorous single-agent (framework-fastapi) ground-truth set: 11
  planted items in a real 1465-LOC dashboard slice, **S-items (should fire) vs B-items (bait,
  must stay silent)**, a mechanical PASS gate, N=3 stability protocol, three-state noise
  rubric. The B-item design measures **false-positive resistance**, which is the sophisticated
  part and the thing H-CORE lives or dies on.
- Per-version RESULTS docs with per-item scores (express 95, vue 97, angular 93, electron
  100, RN 91; control run = 0 survivors — non-vacuous silence proof).

**What's missing (Phase B3 fills this):**
- It's **single-agent, single-repo, manually scored**. The owner's chosen ground-truth source
  — **real past diffs with known outcomes** — extends it to the languages/frameworks the
  answer key doesn't cover, and vibe-check's own memory already catalogs known-outcome diffs
  (the DOGFOOD WIN entries, the 12-DOGFOOD-FINDINGS backlog).
- **Fable attacks the answer key itself:** is the S/B classification *correct*? If Fable
  disagrees that B4 (public `/health`, no auth) is a non-bug, that's either a real vibe-check
  blind spot or a flaw in the key — either is a finding.

---

## How the three Fable passes map to the targets

| Pass | Targets | Artifact (Phase B) | Ground truth |
|---|---|---|---|
| **B1 — cold code review (v2.7)** | Set A (esp. A1 tie-break; the cross-file `70` drift) | code-review prompt | failing test proves/refutes |
| **B2 — design review (v2.8 LOCKED)** | Set B, filtered to what v2.8's frozen decisions touch (`config-as-vehicle`, `scoring-formula-untouched`, `enforcement-split-by-knob`) + H-CORE | falsifiable-hypotheses doc extracted from the committed v2.8 design spec | routes to extended efficacy retro |
| **B3 — product quality** | Set C | extended ground-truth harness (answer-key + real diffs) | S/B catch & FP rates vs known answer |

## Notable facts that de-risk the plan

- **Install is NOT stale** — cache `2.7.0` == repo `plugin.json 2.7.0`. Running vibe-check for
  B3 runs the version Fable reviewed.
- **vibe-check already has committed per-milestone design-rationale docs**
  (`docs/superpowers/specs/*-design.md`). B2 *extracts hypotheses from* the v2.8 spec rather
  than authoring rationale from scratch — cheaper and grounded.
- **`.planning/` is gitignored** (same clobber-class hazard as julian-orchestrator). These
  design docs go under committed `docs/design/`, not `.planning/`.

## Open decision for the owner (before B2/B3)

The v2.8 design is mid-flight (Phase 32 next). B2 reviews only the **LOCKED** decisions so
Fable can inform the *remaining* phases without reviewing WIP. Confirm which frozen decisions
are genuinely open to challenge vs truly closed — the leverage map treats
`scoring-formula-untouched` as the most interesting one to stress-test, because H-CORE and
every magic-number hypothesis in Set B implicitly question whether "never re-weight" is right.
