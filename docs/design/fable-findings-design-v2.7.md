# Fable design review (B2) — vibe-check hypotheses + answer-key attack

**Scope:** the design review (Pass B2) — challenges to the `design-hypotheses.md` §A/§B set, plus
an attack on `docs/efficacy/ANSWER-KEY.md`'s S/B classification. NOT a code-bug hunt (that's B1,
`fable-findings-{score-py,bash}-v2.7.md`).

**Checkout:** verified against tag `v2.7` (baseline scorer + agents) AND
`feat/framework-skill-reviewer` (the v2.8 knob implementation — min_confidence / idiom_floor /
vibe-ignore / thresholds live there, phases 30–32).

## Provenance
**Genuine Fable** — this pass did NOT trip the safeguard model-switch (design content, no
security-bypass framing). The reviewer's own provenance note confirms it verified code-level
claims against both v2.7 and the feat branch. So this IS a real independent cross-model data
point — the payoff the whole review exercise was designed to get. It is the strongest of all
passes: 6/7 §A hypotheses challenged, all 4 §B, all with fixtures.

## Independent verification (Opus, 2026-07-01)
The two act-now findings were re-checked against real code; the rest are design challenges whose
falsifiable form is sound and which route to the efficacy harness (B3) to settle empirically.

| ID | Challenge | Verdict | Act-now? |
|---|---|---|---|
| **NEW-ABSORB** | dedup deletes the losing member into neither findings nor filtered | ✅ **CONFIRMED REAL (HIGH)** — code comment says so | **YES** |
| **H-KNOB kill-shot** | spec's own `min_confidence=60` > documented critical floor (conf≥50) → silently kills real criticals | ✅ **CONFIRMED REAL** | **YES** |
| H-CORE | "agents over-report, scorer filters" mis-states the shipped system (filtering is largely agent-side, in unverified prompt text) | ✅ Legitimate reframing | design |
| H-DUP1 | +10 twin rewards *correlated* error (same base model, overlapping checklists) → rescues borderline FPs | ⏳ Sound; harness settles | harness |
| H-DUP2 | conceded lenses differ, but they double-report in practice; want a render-group | ⏳ Sound | harness |
| H-LANE | lanes overlap on their face — bugs.md resource-leak vs RN native-cleanup for ONE listener leak, no shared attribution, even under perfect obedience | ✅ Structurally confirmed | design/harness |
| H-COUPLE | config DOES influence a surviving finding's score via cross_confirmed set membership → "config only relabels/filters" is false; restate as "zero-config is byte-identical" | ✅ Correct (follows from H-KNOB fixture 2) | design |
| H-CODEX-TRUST | (1) codex conf rides in floor-free → can win dedup representative slot → codex `fix_hint` to the autonomous fix agent; (2) sanitization is title/summary-only, `problem`/`fix_hint` unsanitized yet flow to REVIEW.md + fix prompt | ✅ Both holes real | design |
| O-EXTRACT | mostly conceded; family-3 drift (fix.md title class vs codex display sanitizer) is live, not hypothetical | ✅ concede + 1 exhibit | — |
| O3 | post-fix verify: region-reread misses a fix needing an out-of-region call site; typecheck/test is the only non-LLM reader | ✅ conceded, highest O-priority | design |
| B-SEV / B-XCONF / B-PROX / B-REWEIGHT | §B — all challenged w/ fixtures; B-REWEIGHT has repo evidence (RESULTS same item conf 22/57/42, 35-pt spread) | ⏳ Parked (post-v2.8), all falsifiable | parked |

---

## Act-now finding 1 — NEW-ABSORB: dedup silently deletes distinct real findings  [HIGH]

`score.py:806-807` (cross_confirm_group survivor selection). **Confirmed by the code's own comment.**

STEP A of `cross_confirm_group` unions any two findings with same `file`, `|Δline| ≤ 2`, and same
coarse domain — INCLUDING two DIFFERENT defects (even from the same agent). Then the survivor loop:
```
scored_members.sort(key=lambda t: t[0], reverse=True)
best_score, best_member, best_decision = scored_members[0]
# Members that lost the dedup are absorbed into the survivor (not emitted).   ← score.py:807
```
The non-representative members are appended to **nothing** — not `survivors`, not `filtered`. They
vanish without a trace. Two co-located same-domain bugs collapse to one; the second is
unrecoverable.

- **Pure test_score.py fixture (no LLM needed):** language-python reports `mutable-default` at L10
  and `bare-except` at L11 — both map to `style`, within ±2, same domain → union → one reported,
  one gone. Worse in security: `injection@L10` + `secrets@L11` → one reported.
- **Why it's a real defect, not a debate:** it directly contradicts the design's load-bearing
  "never silently drop" principle (`bugs.md:21`: "a silently dropped real issue is
  unrecoverable"). The scorer's own comments repeatedly cite silent-absorption as the reason NOT
  to map more categories — but the hazard is already live among the mapped ones.
- **Within-lock fix:** absorbed members must land in `filtered[]` with `reason: "absorbed-into:
  <survivor-hash>"`. Dedup bookkeeping, not a weight change.

## Act-now finding 2 — H-KNOB kill-shot: `min_confidence` above the critical floor silently annihilates real criticals  [HIGH]

`ANSWER-KEY.md:25` + spec `design.md:53` + `config.py:90`. **Arithmetic confirmed.**

- `ANSWER-KEY.md:25` documents a **critical surfaces at conf ≥ 50** (50 + 20 in_diff + 0 severity
  = 70 = surface floor).
- The spec's illustrative config (`design.md:53`) is **`min_confidence = 60`**.
- `config.py:90` validates `min_confidence` over the full **`[0, 100]` with NO warning** at any
  value.

So a repo configured *exactly as the spec's own example shows* silently drops every critical whose
agent confidence is 50–59 — findings v2.7 surfaced at score 70–85. Because `min_confidence` filters
**before** scoring (and before `cross_confirm_group`), nothing can rescue them: the trust-adders
(in_diff +20, cross-confirm +10) never run. This is the literal v2.8 definition-of-done violation
("nothing real silently vanishes"; visible-in-summary ≠ surfaced-for-adjudication).

- **Fixture:** re-run the fastapi fixture with an S1-class critical forced to conf ~55 and
  `min_confidence=60` → v2.7 surfaces it at 75–85; v2.8 routes it to `filtered: below-min-confidence`.
- **Within-lock fix:** `config.py` warns (or refuses) when `min_confidence ≥ 50` (at/above the
  critical floor). Also fixes the compounding H-COUPLE issue (config DOES change a surviving
  finding's emitted score via which twins survive to cross-confirm — so the doc's "config only
  relabels/filters" claim is false; restate as "zero-config output is byte-identical").

---

## Answer-key findings (attack on ANSWER-KEY.md's S/B classification)

The one existing efficacy fixture (`docs/efficacy/ANSWER-KEY.md`, framework-fastapi, 11 items).
These are gaps in the *ground truth itself* — a flawed answer key mis-measures every future run.

### AK-1 — The "one mechanical line" is not mechanical (under-specified gate)  [Medium]
`ANSWER-KEY.md` PASS gate "B1–B5 all stay < 70" doesn't say whether a bait fails on ANY finding
≥70 *at its site*, or only on the *planted axis*. RESULTS run-1 surfaced missing-auth on
`ping_host` — B1's exact route — and the tool ruled it "coverage upside" via axis-scoping the gate
line never states. Under a strict site reading, EFF-02 was NOT a clean 3/3. **Not a tool
misbehavior** (the auth finding is real) — the *bar* is ambiguous in the one place it claims to be
mechanical. **Fix:** state the gate as axis-scoped, and require per-run diagnostics to tag every
≥70 finding at a bait site as `{planted-axis-suppressed | off-axis-real | off-axis-FP}`.

### AK-2 — B1's "NOT a bug" classification is false as written  [Medium]
B1 (sync call in a plain `def`) is labeled globally non-buggy because plain-def threadpool dispatch
makes the *async axis* safe. But `requests.get(...)` with no timeout inside a threadpool route is a
real **thread-pool-exhaustion** defect under load (default ~40 threads, unbounded outbound call).
B1 is only a good bait *under axis scoping*; the key currently trains the fleet that the whole route
is safe. **Fix:** re-classify B1 as axis-scoped (async-safe, but not globally safe).

### AK-3 — B4 enshrines a gameable exemption  [Medium → High as a fleet-training risk]
D-09 exempts auth findings by endpoint **name** (`/health`, `/healthz`, `/metrics`). **Content, not
name, determines safety.** Name a data-leaking route `/health` and the fleet is trained to stay
silent. **Counter-fixture:** a `/health` route returning full machine rows incl. encrypted-secret
columns — if the agent stays silent, D-09 is a blind spot the answer key *rewards*; if it fires,
the exemption is being applied with content judgment and the key should say so. This is the
sharpest answer-key finding — it's an exploitable false-negative baked into ground truth.

### AK-4 — B3 encodes an over-broad "passthrough = safe" gate  [Medium]
B3 ("dict passthrough with no key access = intentional") is sound for the *validation axis as
planted*, but as a general gate it encodes "code that doesn't inspect its input is fine" — exactly
how relay-shaped SSRF/injection ships. **Variant fixture:** same relay, but the dict feeds a URL or
command construction in-slice — the gate must NOT suppress that.

### AK-5 — Meta: the answer key tests only agent-side gates  [structural]
All five baits (B1–B5) test *agent-side* silence discipline; **none tests the scorer path** —
cross-confirm noise (H-DUP1), absorption (NEW-ABSORB), or the v2.8 knobs (H-KNOB). Yet the fixture
is cited as evidence for the *pipeline's* signal:noise (H-CORE). The answer key needs a second half:
scorer-path baits. (The §A fixtures in this review are, in effect, that missing half.)

### AK-6 — S4 non-catch is the agent-level analog of NEW-ABSORB  [note]
S4's honest non-catch (the agent spent its finding-slot on the co-located higher-severity auth
issue) is agent-level absorption — worth a named line in the key, not a footnote. Conceded items:
S1–S3, S5, V1, and **B5 (excellent bait — Pydantic deep-copies field defaults, the #1 Python-model
FP)**.

---

## Routing
- **Act now (within lock):** NEW-ABSORB (filtered-bookkeeping fix), H-KNOB (config.py warn ≥50).
  Both can inform the remaining v2.8 phases.
- **Design (within lock, needs decision):** H-CORE reframe, H-CODEX-TRUST holes, H-COUPLE restate,
  O3 post-fix verify, the answer-key fixes AK-1–AK-5.
- **Parked (post-v2.8, §B):** B-SEV, B-XCONF, B-PROX, B-REWEIGHT — all falsifiable via the B3
  harness (which is also where H-DUP1/H-DUP2/H-LANE get settled).
- **Variant-D:** Fable confirmed availability for B3 with a protocol request — give it the diffs
  WITHOUT the answer expectations, score both reviewers against the same post-hoc adjudication so
  neither is anchored.

## Cross-references
- Hypotheses attacked: `design-hypotheses.md`
- The attacked ground truth: `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md`
- B1 code findings: `fable-findings-score-py-v2.7.md`, `fable-findings-bash-v2.7.md`
- B3 harness (where §B + H-DUP settle): `b3-ground-truth/B3-STATUS.md`, `product-quality-harness.md`
