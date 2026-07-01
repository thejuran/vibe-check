# Pass B4 — Per-subagent efficacy (Stage 1: prompt-quality critique)

> **Status:** Opus, 2026-07-01. The pass that fills the gap between B2 (fleet *architecture* —
> do overlapping agents earn their place?) and B3 (tool-level *aggregate* catch/FP rate). Neither
> measures **per-agent** efficacy: does the `security` agent catch security bugs and stay quiet
> otherwise? does each `framework-*`? vibe-check has efficacy-tested exactly ONE of ~12
> specialists (`framework-fastapi`, the 11-item S/B ANSWER-KEY). This pass covers the rest.
>
> **Two stages, by owner decision (2026-07-01):**
> - **Stage 1 (this doc):** Fable critiques each agent's `.md` prompt AS A SPEC — fast, no runs,
>   surfaces which agents are noise-generators or miss-prone by construction, and **tells us
>   where to aim the expensive fixtures.**
> - **Stage 2 (later):** build per-agent catch-rate / false-positive-rate fixtures (the
>   ANSWER-KEY method generalized), focused where Stage 1 flagged risk.
>
> **The framing fact:** every detection agent is told "Coverage, not filtering" — over-report,
> don't self-filter (`bugs.md:19-21`); NO detection agent references `false-positive-rules.md`;
> ALL noise suppression is orchestrator-side. So each agent is deliberately tuned to over-report,
> and the design bet is that centralized scoring cleans it up. Stage 1 judges each agent against
> THAT bet: is its rubric precise enough that over-reporting is useful rankable signal, or so
> loose it floods the scorer with noise it can't distinguish from real findings?
>
> **Provenance note:** the roster includes the `security` agent, so Fable's content-safety
> safeguards *may* switch this to Opus mid-run (as happened on the bash pass). If so, record it
> as Opus-authored — still useful, just not a cross-model data point.

## Roster (v2.7, sizes for calibration)

12 specialists + core/meta: bugs (61), security (85), architecture (54), compliance (34),
impact (47), test-sufficiency (114), triage (33), language-typescript (43), language-python (41),
language-go (38), language-rust (37), framework-react (62), framework-vue (148),
framework-angular (148), framework-express (146), framework-fastapi (127), framework-electron
(177), framework-react-native (93), framework-skill (98).

---

## Copy-paste prompt (Stage 1 — run in a FRESH Fable session, `git checkout v2.7` first)

```
You are Fable, a second frontier model, auditing the QUALITY of vibe-check's subagent prompts.
vibe-check reviews git diffs by dispatching ~19 specialist subagents (bugs, security,
architecture, compliance, impact, test-sufficiency, triage, language-{typescript,python,go,rust},
framework-{react,vue,angular,express,fastapi,electron,react-native,skill}). Each agent is a
markdown prompt in plugins/vibe-check/agents/*.md. The orchestrator dispatches them in parallel,
collects their JSON findings, and scores/filters. Your job: judge each agent PROMPT AS A SPEC —
will it, by construction, produce good findings (real issues caught, non-issues left alone), or
will it produce misses and noise? This is a design critique of the prompts. No code execution,
no fixtures, no runs. Report only; edit nothing.

## The one structural fact that frames everything
Every detection agent is told "Coverage, not filtering" — report EVERY issue, do NOT self-filter
for importance or confidence (see bugs.md:19-21). No detection agent references
false-positive-rules.md; ALL noise suppression is delegated to the orchestrator's scorer. So each
agent is deliberately tuned to OVER-REPORT. The design bet is that centralized scoring cleans it
up. Your critique should judge each agent against THIS design: given that it's told to
over-report, is its rubric precise enough that its over-reporting is USEFUL signal the scorer can
rank — or is it so loose/vague that it will flood the scorer with noise it can't distinguish from
real findings (false confidence, miscategorization, taste dressed as defects)?

## Read
- plugins/vibe-check/agents/*.md — all of them (they're 33–177 lines each).
- plugins/vibe-check/templates/agent-output-schema.md — the JSON contract each must emit.
- plugins/vibe-check/templates/scoring.md — how the orchestrator scores what they return
  (so you can judge whether an agent gives the scorer what it needs: honest agent_confidence,
  correct severity, a category the scorer's cross-confirm map recognizes).
- plugins/vibe-check/templates/false-positive-rules.md — the noise rules the agents DON'T
  reference (judge whether each agent should).

## Per-agent, assess these dimensions
1. **Rubric precision** — are the "what to flag" criteria concrete and testable, or vague
   ("looks wrong", "poor design")? Vague rubric + over-report mandate = noise generator.
2. **Category discipline** — are the agent's finding categories well-defined and mutually
   distinct, or overlapping/ambiguous (so the same defect lands in different buckets run to run,
   defeating cross-confirm)?
3. **Confidence calibration guidance** — does the prompt help the agent assign an HONEST
   agent_confidence (the scorer's key input), or will it emit uniformly high/low confidence that
   makes the scorer's job impossible?
4. **Severity guidance** — clear mapping to critical/high/medium/low, or left to the agent's
   whim?
5. **False-positive exposure** — what specific non-bugs will THIS agent flag by construction
   (framework idioms it will misread, safe patterns it will call defects)? Name them. This is
   where the over-report mandate bites hardest.
6. **Scope creep / overlap** — does it stray into another agent's lane (e.g. language-typescript
   and framework-react both on hooks; architecture and impact on structural change), producing
   duplicate or contradictory findings?

## Deliverables
1. A per-agent scorecard: agent | rubric-precision (H/M/L) | biggest false-positive risk (named)
   | biggest miss risk (named) | one concrete prompt fix.
2. A ranked list: which agents are MOST likely to be noise generators, and which are MOST likely
   to MISS real issues — the two failure modes the owner (a PM who can't read code, relying on
   this as his sole reviewer) most needs to know about.
3. The bridge to empirical testing: for the 3–5 highest-risk agents, name the specific planted
   true-positive (should-fire) and bait non-bug (should-stay-silent) cases a fixture should
   include to MEASURE the risk you identified. (This seeds a later per-agent catch-rate /
   false-positive-rate harness — you're telling us where to point it.)

## Output format
Scorecard table first, then the two ranked failure-mode lists, then the fixture-seed
recommendations. Ground every claim in a specific line of the agent's .md file. Report only.
```

## How Stage 1 results route

- Deliverable 3 (fixture seeds for the top 3–5 risk agents) becomes the input to **Stage 2** — a
  per-agent catch/FP harness generalizing `docs/efficacy/ANSWER-KEY.md` beyond framework-fastapi.
- Findings that are really *design* challenges (an agent's whole rubric is wrong) route to the
  B2 design review's efficacy method, not a fixture.
- When results come back, verify each against the actual agent `.md` line cited (same discipline
  as the B1 findings: does the code/prompt actually say what the critique claims?), then save
  alongside `fable-findings-*.md`.

## Cross-references
- Fleet architecture hypotheses (H-DUP1/H-DUP2/H-CORE): `design-hypotheses.md`
- The one existing per-agent ground truth: `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md`
- Tool-level aggregate metric: `product-quality-harness.md`
- Leverage context: `fable-review-leverage-map.md`
