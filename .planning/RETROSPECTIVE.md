# Retrospective: vibe-check

Living retrospective across milestones. Newest milestone sections are added above the Cross-Milestone Trends section.

## Milestone: v2.2 — Codex adversarial reviewer

**Shipped:** 2026-06-21
**Phases:** 3 (4-6) | **Plans:** 6 | **Commits:** 24 (v2.1..v2.2)

### What Was Built
Codex (GPT-5-codex) as a second, independent adversarial reviewer in `/deep-review`: a contract agent (`codex-adversarial.md`), an orchestrator Codex step in `deep-review.md` (probe → exact-or-skip diff targeting → background launch with a self-contained 300s watchdog → translate → join at Phase 3 entry → cross-confirm +10 → skip-and-note degradation), and a selection-matrix row. Additive, prompt-only, four core files byte-unchanged (MERGE-01). plugin.json 2.1.0→2.2.0, annotated tag v2.2.

### What Worked
- **Cross-model review on the plan caught real holes the plan-checker passed.** The gsd-plan-checker PASSED Phase 6's plan; Codex adversarial review then found 4 high + 1 critical across three passes (auth-restore not actually guarded, weak-run could ship EFF-01-only, sign-off substring bypass, false-green release verify, tag-not-bound-to-commit). Complementary signal, not redundant.
- **Planting a defect in a throwaway branch made EFF-02a deterministic.** Both planted defects (SQLi + null-deref) cross-confirmed +10 on the first authenticated run — no D-06 fallback needed.
- **The efficacy test doubled as the integration check.** The live `/deep-review` run exercised the full Phase 4→5→6 chain end-to-end, which is stronger evidence than a static integration-checker pass.
- **Recovery-first auth invariant + fingerprint check** meant the de-auth proof never risked leaving the user logged out (once the broker-pin gotcha was found).

### What Was Inefficient
- **The de-auth recipe was wrong twice before it worked.** Research said "move auth.json aside"; that was insufficient (broker caches the session). Even after broker teardown + move-aside, *restore* stayed `ready:false` until the per-project broker pin under `~/.claude/plugins/data/codex-openai-codex/state/<project>/broker.json` was cleared. Cost a few diagnostic cycles; now captured to memory.
- **Two zsh unquoted-glob errors** (`*/broker.json`, `broker*.json`) aborted shell steps mid-way; switched to `find`.
- **The SDK's auto-extracted milestone accomplishments were garbage** (pulled deviation-log lines); had to hand-write the MILESTONES.md entry.
- **3 adversarial rewrite passes + 1 over-cap pass** on the plan — worth it for irreversible auth/tag ops, but the last critical (gitignored approval state) was un-closeable at the plan level and only recognized as such after a 4th pass.

### Patterns Established
- **Exact-or-skip external-reviewer diff targeting** — run the external tool ONLY when its representable range provably equals the orchestrator's resolved diff; else fail closed to skip-and-note.
- **Join translated external output at Phase 3 entry** so it rides every merge/dedup/score step like a native agent (cross-confirm for free).
- **Release-gate verification reads from the tagged commit (`v2.2^{commit}`), never the working tree** — closes the accidental-false-green class.
- **Live human checkpoint covers what gitignored state can't bind** — for release gates, accept that `.planning/` approval state can't be cryptographically tied to the tag; rely on the in-session sign-off.

### Key Lessons
- Cross-model adversarial review on the *plan* (not just the code) earns its cost on phases with irreversible operations.
- When de-authenticating a cached/brokered companion, the credential file is not the only state — find and clear the broker/session pin, and verify restore with a no-secret fingerprint.
- Reuse the prior milestone's release shape (v2.1 → v2.2: plugin.json bump + annotated tag) as the template; it removes guesswork.

### Cost Observations
- Model mix: opus on the heavy reasoning (researcher, planner, plan-checker was sonnet, native bugs/architecture/impact opus); Codex (GPT-5-codex) for the adversarial passes + the live efficacy review.
- Sessions: 1 (this milestone run, resumed at Phase 6 from prior-session Phases 4-5).
- Notable: most tokens went to the 3-pass adversarial hardening of a 3-plan validation phase — high ratio of review-to-build because the build was tiny (a version bump) but the operations were irreversible.

## Milestone: v2.5 — Sharper, more legible reviews

**Shipped:** 2026-06-28
**Phases:** 4 (19-22) | **Plans:** 8 | **Commits:** 42 (v2.4..v2.5)

### What Was Built
`--all` that reviews *source, not noise* (a docs/planning denylist + a code-`.md` allowlist
override in `templates/skip-rules.md`, consumed by `review.md`'s mode-5 selection with an
`--include-docs` escape hatch; bare `all` accepted; one-line `Mode:` conclusion). The deterministic
core `score.py` crash-proofed against malformed agent output (container guard, `_safe_window`,
non-finite-confidence guard, fail-closed envelope) and pinned by a T1-T21 malformed-shape matrix. A
new deep-review-only **test-sufficiency agent** — a consume-only coverage reader that risk-weights
gaps and skips-and-notes when no coverage data exists, with the coverage responsibility carved out
of `impact.md`. plugin.json 2.4.0→2.5.0, annotated un-pushed tag `v2.5`.

### What Worked
- **The dogfood caught two real cross-file-drift defects in the tool's OWN contracts** — a
  `review.md` finalize-loop reading `medium_acknowledgments` from a per-pass path nothing writes,
  and a `framework-react` category drift that blocked React↔TS cross-confirm. The exact bug class
  the tool exists to catch, found by pointing the tool at itself. Owner asked to fix before sign-off.
- **The Phase-22 review caught my *fix* over-reaching.** The first React fix mapped all four React
  categories to the broad `style` domain — which would have let an `a11y` finding silently absorb an
  unrelated co-located `type-safety` finding. The review gate drove a tighter correction (map only
  the genuine `hooks`↔`react-hook` twin). The process caught its own mistake before tagging.
- **Verifying the fix end-to-end with a constructed cross-confirm case** (hooks+react-hook still
  merge; a11y+type-safety stay separate) gave hard evidence the tightening was right, not just
  plausible — and became two regression-lock tests the integration check recommended.
- **The frozen golden digest stayed unmoved through every score.py change**, proving each was
  behavior-preserving for existing fixtures.

### What Was Inefficient
- **The moving-HEAD / DOGFOOD_HEAD reconciliation cost real care.** The dogfood ran on one commit,
  then in-milestone fixes + a review tightening + a regression test each moved the runtime source,
  so the tag's source-parity gate (tag must stamp byte-identical runtime to DOGFOOD_HEAD) kept
  failing until DOGFOOD_HEAD was repointed to the last runtime-touching commit and the three threads
  re-confirmed there. Honest, but several extra sync+verify cycles.
- **The install cache needed re-syncing four times** as HEAD advanced through fixes/review/docs —
  each a clean-build-from-committed + `diff -r` + registry repoint. Correct, but repetitive.
- **The orchestrator path produces no per-phase VERIFICATION.md**, so the milestone audit had to
  establish satisfaction from SUMMARY frontmatter + dogfood + integration-check (the v2.4 precedent)
  rather than the audit workflow's assumed per-phase verifier output.

### Patterns Established
- **The dogfood is allowed to expand the close.** When the self-review finds real defects, fixing
  them in-milestone (then re-verifying) is the right call — it's the whole point of dogfooding a
  review tool, not a scope violation.
- **Review the fix, not just the original.** A surgical fix that bypasses the per-phase gate gets
  its own focused review before tagging — the gate caught a silent-drop regression a "tiny diff"
  intuition would have shipped.
- **Map only genuine cross-agent twins in CATEGORY_DOMAIN.** A coarse shared domain merges (and
  absorbs) unrelated co-located findings; only categories that are true twins of another agent's
  category should share a domain. Locked with a regression test.
- **DOGFOOD_HEAD names the last runtime-touching commit, re-confirmed.** When post-dogfood fixes
  move the runtime source, repoint DOGFOOD_HEAD and re-run the thread checks there — never let the
  tag claim efficacy-proven over un-dogfooded code.

### Key Lessons
- A review tool pointed at itself is the strongest efficacy test there is — but only if you actually
  fix what it finds and then re-review the fix.
- Source-parity gates between "what was dogfooded" and "what gets tagged" are worth the friction:
  they force the provenance to stay honest when the tree moves under you.
- Tightening is safer than broadening for cross-confirm: prefer the conservative twin-only mapping
  and let a co-located finding stand alone rather than risk a silent absorption.

### Cost Observations
- Model mix: opus on the close-review (bugs + architecture agents), integration checker, and the
  orchestration; the dogfood ran the deep `--all` roster (bugs/architecture top-tier, impact +
  test-sufficiency opus, the rest sonnet). Codex fail-closed on the whole-repo `--all` range (no
  adversarial pass this milestone).
- Sessions: 2 (Phases 19-21 in a prior session; Phase 22 close resumed post-relaunch, spanning a
  context compaction).
- Notable: a high review-to-build ratio at the close — the build was small (a denylist, guards, one
  agent, a version bump) but the dogfood-found fixes + the review-of-the-fix + the tag source-parity
  reconciliation carried the token weight.

## Milestone: v2.9 — Prove it

**Shipped:** 2026-07-08
**Phases:** 3 | **Plans:** 6

### What Was Built
33-02 codex wiring made live (LEGIBLE-01/02/03) + all deferred v2.8 smoke proofs (PROOF-01/02); the committed pre-registered B3 ground-truth kit + 18 owner runs → first measured numbers (catch 8/9, FP 6/9, D-11 verdict); the v2.9.0 close with atomic hash-verified publish.

### What Worked
Pre-registration made the numbers provable (key-blob digest + manifest ordering survived every audit re-derivation). Findings-scoped adversarial rewrites converged where full-plan ones historically ballooned. The atomic-push + exact-hash publish gate executed clean on the fresh path, zero STOPs.

### What Was Inefficient
The phase-37 adversarial loop ran 10 passes / 9 rewrites — most post-pass-4 findings were codex red-teaming the resume scaffolding the rewrites themselves added (bookkeeping corners, rc-masking family). Cap-bump pauses worked as designed but the tail cost real wall-time. Phase 35's wrapper session skipped the verifier — caught only at milestone audit (retroactive verification closed it).

### Patterns Established
Classify-then-capture for any state-dependent persistence; rc-preserving capture-then-test for every command-substituted helper; per-commit (not net-diff) leak checks over release ranges; no-checkout local ref push (`git push . branch:main`) for dirty-worktree fast-forwards.

### Key Lessons
The scorer's confidence-driven banding produced live FPs during this milestone's own close review (impact affirmations banded critical/warning) — the exact B-SEV/H-CORE behavior the B3 numbers quantified. Next milestone's scoping input is already measured.

### Cost Observations
- Model mix: opus-heavy (planner/executor/verifier + deep-review top tier), sonnet checkers, haiku triage
- Sessions: 4 across the milestone (checkpoint-resumed cleanly at every /clear boundary)
- Notable: codex adversarial passes ~5-8 min each; 10-pass gate ≈ half the phase-37 wall time

## Cross-Milestone Trends

| Milestone | Phases | Plans | Shipped | Efficacy |
|-----------|--------|-------|---------|----------|
| v2.1 FastAPI review agent | 3 (1-3) | 3 | 2026-06-18 | EFF-02 PASS (N=3, 3/3 criticals) |
| v2.2 Codex adversarial reviewer | 3 (4-6) | 6 | 2026-06-21 | EFF-01/EFF-02 PASS (2 cross-confirms, de-auth degraded) |
| v2.5 Sharper, more legible reviews | 4 (19-22) | 8 | 2026-06-28 | CLOSE-01 PASS (`--all` self-dogfood, owner sign-off, 2 self-defects caught + fixed) |

**Recurring pattern:** every milestone closes with an efficacy test + owner sign-off as the human
bar — the right verification shape for a prompt-only review plugin where coverage, not unit tests, is
the contract. From v2.3 on, that efficacy test is the tool dogfooding itself on its own codebase;
v2.5 is the first where the dogfood found real self-defects that were fixed before sign-off rather
than deferred.
