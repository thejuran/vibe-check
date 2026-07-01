# Fable agent-efficacy audit (B4) — subagent prompt quality (v2.7)

**Scope:** Pass B4 — a design critique of the 18 detection-agent prompts AS SPECS (security.md
excluded by instruction; gets its own pass). Judges whether each agent's rubric, given the
"Coverage, not filtering" over-report mandate, feeds the scorer *rankable* signal or unrankable
noise. No runs.

**Checkout:** verified against tag `v2.7`.

## Provenance
**Genuine Fable, clean start-to-finish** — skipping `security.md` avoided the content-safety
switch that hit the bash pass. Real independent cross-model data point.

## Independent verification (Opus, 2026-07-01)
The central thesis and the most damaging specific claims were checked against real agent files.
**All confirmed; nothing overstated.** This is the most directly ACTIONABLE pass of the review.

### The central thesis — CONFIRMED against code
> "The fleet is two generations of prompt, and the scorer can't tell them apart."

Grep of calibration/hedge markers (off-hunk ceilings, `≤40`/`≤45`, `pending:`, SAFE lists,
confidence anchors) per agent:

| Generation | Agents | Calibration markers |
|---|---|---|
| **Gen-2** (calibrated) | framework-vue / angular / electron / fastapi (+ express, react-native, skill, test-sufficiency) | **19–30 each** |
| **Gen-1** (uncalibrated) | bugs, architecture, compliance, impact, framework-react | **0 each** |
| Gen-1 (near-zero) | language-typescript (3), python (1), go (1), rust (4) | incidental only |

**Why it bites (verified):** with `+20 in_diff` (scoring.md:14) and bugs.md:49's *only*
confidence example being `95`, an uncalibrated agent lands findings in Warning/Critical bands —
which per **scoring.md:50-51 "enforce — blocks finalize, NO acknowledgment path."** So gen-1
noise isn't clutter the scorer cleans up; it's **enforcement-grade output the scorer structurally
cannot discount**, because its only discounting inputs (agent_confidence, severity) are the exact
fields these agents get no guidance on. Confirmed spot-checks: language-go:17-18 (idiomatic
blocking channel-send + Go-1.22-fixed loopvar, no version gate = deterministic FPs);
architecture:20-28 (rubric is literally questions, not criteria).

## The headline (verified, act-now)
The single highest-leverage fix is **NOT new checks** — it's retrofitting the Gen-2 calibration
block (per-check severity tags, off-hunk confidence ceilings, SAFE never-flag lists, a 3-point
confidence-anchor example) onto the 8 gen-1 agents — starting with **bugs, architecture,
compliance, and the four language agents**. The framework fleet already proved the pattern out.
This converges with B2's AK-5 (the answer key only tests agent-side gates): 8 agents have no
agent-side calibration at all, and nothing currently measures them.

---

## Per-agent scorecard (verbatim from the audit; line refs are the agent .md files)

| Agent | Rubric | Biggest FP risk | Biggest miss risk | One fix |
|---|---|---|---|---|
| bugs | L | Confident null-access/leak where guard is off-hunk (no hedging exists); "race conditions" fired on single-threaded async | Plain logic errors (inverted cond, wrong operator) have no category home (7-item list :25) | Retrofit gen-2 off-hunk rule + add logic-error category + replace the conf-95 example (:49) with a 3-example spread |
| architecture | L | Rubric is questions not criteria (:32,:36); Opus + over-report + no severity guidance = taste at high scoring 100 | Design domain has ONE emitter → no arch finding can ever cross-confirm (score.py:339-342) | Per-category severity table (duplication/pattern-consistency cap medium) + testable gates (dup needs ≥3 instances) |
| compliance | M | Qualified rule applied as absolute, ×+20 citation bonus (scoring.md:15): 55+20+20−8=87 Warning, unack | must/must-not gate (:19) skips imperative rules with no modal verb | Confidence rubric keyed to match quality; state in-file the +20 lifts bands ~40pts |
| impact | M | perf-at-scale speculation as located defects, schema unseen | Highest-value output routed to agent_notes (:33) which never scores/bands | Confidence anchors mirroring severity table; ship-changing notes must also emit a file-level finding |
| test-sufficiency | H | Line-level gaps from a coverage artifact predating the diff (stale by construction in diff-mode) | Shifted lines make real gaps invisible; role-by-filename mislabels | Staleness rule: hedge line-level claims when artifact provenance predates the diff |
| triage | H/L | Over-emission well-guarded (import gates) | A dropped carve-out from the ~1,300-word single-bullet para (:27) run by Haiku silently disables a whole lane | Restructure :27 into a per-framework table (signal→emit/supporting/never) + examples |
| language-typescript | L/M | "Missing try-catch around await" (:18) flags idiomatic propagate-to-boundary; linter territory (:13,:25); inline-fn taste (:30) | async-discipline→style but bugs' error-handling→correctness, so floating-promise can never +10 | Delete linter bullets; gate try-catch to "no upstream handler"; remap async-discipline→correctness |
| language-python | M | Pydantic mutable-default (fleet's #1 FP) guarded only in fastapi.md:45; this co-dispatches on FastAPI diffs unguarded | No async checks at all | Copy the Pydantic carve-out here; demote type-hints/__main__ to low w/ convention gate |
| language-go | L/M | "Channel sends without select+default" (:17, flags idiomatic blocking sends); loopvar (:18, fixed Go 1.22, no gate) = deterministic FPs | Deliberate vs accidental `_ = err` indistinguishable (:10) | Delete/invert channel bullet; version-gate loopvar to go.mod<1.22 + off-hunk hedge |
| language-rust | L/M | Taste as defects: Arc<Mutex>→RwLock (:20, needs workload), .clone() cascades (:12), blanket unwrap (:11 incl main/build) | unsafe review is "has a // SAFETY comment" (:10) — presence not soundness | Pin Idioms section (:24-27) to low; carve out unwrap in main/tests/examples/build.rs |
| framework-react | M | Only framework agent never retrofitted: inline JSX literals wholesale (:19); deps-array asserted when deps off-hunk | "Stale closures over state" (:15) genuinely hard from a diff, no confidence steer | Retrofit vue/angular ceiling + SAFE list; gate inline-literal to memoized children/list items |
| framework-vue | H | Residual/hedged — worst case (:key index, :70-72) already capped medium | By design: off-hunk teardown leaks → ≤40 filtered to a count the owner never reads (:19-22) | Every pending: note must name the exact file/symbol to check |
| framework-angular | H | Minimal — D-03 SAFE list (:87-104) is the fleet's best | Line-37 contradiction ("plausibly off-hunk" always true) can delete the hedged path → rxjs-leaks fires only fully-visible | Rewrite :37 to "present in-hunk"; the ≤40 ceiling already handles plausibility |
| framework-express | H | "3-arg handler clearly meant to be error handler" (:92-93) is intent judgment at HIGH | input-validation unmapped (:123-126) unlike siblings → Express req→sink never +10 with security's injection | Twin input-validation→security (electron precedent) or document why it stays cold |
| framework-fastapi | H | Pydantic-v1 idiom at unknown version emitted ~70 to clear deep-review (:44) — nits in pinned-v1 repos | Category wobble: response-model in both response-status (:51) and openapi-honesty (:70) breaks persist +15 / dedup identity | Drop v1-idiom unknown-version conf to ≤45; disambiguate the boundary |
| framework-electron | H | Explicit nodeIntegration:true on a window loading only bundled local content = headline CRITICAL (:42-45), no SAFE carve-out, no ack path | ipc-validation coarse-domain twin absorbs co-located security finding ±2 (:148-151) — two defects merged (= B2's NEW-ABSORB) | Keep CRITICAL but require the finding to state what the window loads when loadFile/loadURL in-hunk |
| framework-react-native | H | expo-config secret detection is key-name heuristic (:41): pushToken/authScreenSeen match with no secret | Narrow lane: nothing covers bridge/TurboModule misuse or image-memory blowups | Require value provenance, not key-name match |
| framework-skill | H | Bidirectional workflow check (:39) — "no clear sequence" AND "over-constrained" — unfalsifiable taste pair at med/high | Wiring checks trigger only on ADD/RENAME (:50) — a removed agent leaving dangling rows is invisible | Extend wiring to removals; cap the "over-constrained" direction at low ≤45 |

## Ranked: most likely NOISE generators
1. **architecture** — vaguest rubric (question-clusters :19-37) + strongest model + over-report + no severity/confidence guidance + a domain no one else emits (never corroborated). "Is this coupling appropriate?" at high severity + default-high conf scores ≥97 and blocks finalize, in vocabulary the PM can't evaluate.
2. **language-typescript** — highest dispatch volume × one wrong check (:18) + two linter-territory (:13,:25 vs false-positive-rules.md:16-19) + two taste checks. Volume × wrong rubric = largest raw noise stream.
3. **bugs** — every diff, no off-hunk hedging, only example anchors conf 95 (:49); "race condition"/"state mutation" one-liners pattern-match huge amounts of correct async code.
4. **compliance** — +20 citation bonus makes it the highest per-finding amplifier (55→87 Warning) with zero calibration to spend against the leverage.
5. **language-go** — two deterministic-FP bullets (:17,:18) that fire on provably correct idiomatic code.
6. **language-rust / framework-react** (tied) — idiom-as-defect + un-hedged inline-literal/deps-array.

## Ranked: most likely to MISS
1. **triage** — the only agent whose misses are silent AND total: a dropped framework signal → a specialist never dispatches, and nothing records the absence. Excellent rules; entrusting a 1,300-word single-para block to Haiku is the risk.
2. **bugs** — the fleet's only generic reviewer; 7-pattern rubric, no depth instruction, no home for plain logic errors (the most common bug class in LLM-written code) — for the owner's exact use case.
3. **framework-angular** — the :37 contradiction can suppress the whole hedged rxjs-leaks path; the most common leak presentation (diff shows subscribe, not class) surfaces as an unread count.
4. **compliance** — modal-verb gate (:19) skips imperative rules; directory-level AGENTS.md never read (:18 root only).
5. **impact** — "most value" in agent_notes (:33) which never score/band/block → un-locatable blast-radius is structurally advisory.
6. **test-sufficiency** — no staleness concept; artifacts predating the diff (always, for uncommitted changes) produce both phantom and masked gaps.

## Fixture seeds (the bridge to the B3 harness — where to point per-agent measurement)
- **bugs** — fire: null-deref w/ no guard in file + an inverted-branch logic error (instrument the *category* field — there's no correct one). silent: same deref w/ guard 4 lines off-hunk; two unrelated sequential awaits (the "race" false-fire).
- **architecture** — fire: raw fetch+retry in a repo with an established httpClient wrapper used by 5 files. silent/≤med: a 2nd 3-line validation dup (below rule-of-three); a justified new dep (zod at 3 boundary files). *Instrument the severity distribution — the risk is taste emitted at high.*
- **compliance** — fire: "Never log sensitive data" + `logger.info(req.headers.authorization)`. silent: a qualified "only where…" rule with a propagate-to-handler diff. miss-probe (should fire): a modal-verb-free rule violated in-diff.
- **language-typescript** — fire: a genuinely floating promise. silent: await w/ no local try-catch under visible error-boundary middleware; `as UserPrefs` on a literal built 2 lines up; inline arrow to a plain `<button>`.
- **triage** (label harness, not findings) — must emit: async-storage-only→react+react-native; .vue-only→vue; express Router→express. must NOT: expo-server-sdk backend→no RN; Connect-shaped handlers→no express; preload webPreferences w/o electron import→no electron; @Component from non-Angular lib→no angular. Run ~10× — metric is carve-out retention under Haiku; any <100% = rewrite :27 as a table.
- **bonus (near-zero effort)** — a Go fixture with one idiomatic blocking channel send + one loopvar capture under go 1.22; language-go should stay silent and provably won't (:17-18).

## Routing
- **Act now (highest leverage of the whole review):** retrofit the gen-2 calibration block onto
  bugs, architecture, compliance, impact, and the 4 language agents. Not new checks — calibration.
- **Specific bug fixes:** language-go :17-18 (deterministic FPs), framework-angular :37
  (contradiction suppressing rxjs-leaks), framework-react (retrofit hedging), framework-electron
  ipc-validation twin (= B2's NEW-ABSORB, same root).
- **Feeds B3:** the fixture seeds above are the per-agent measurement targets; combined with B2's
  scorer-path baits, they'd finally cover the whole pipeline.
- **security.md** — still owed its own critique (separate pass, likely Opus).

## Cross-references
- The prompt: `agent-efficacy-critique.md`
- Converges with B2 AK-5 (answer key tests only agent-side gates): `fable-findings-design-v2.7.md`
- NEW-ABSORB (electron ipc twin, same root): `fable-findings-design-v2.7.md`
- Where the fixture seeds run: `b3-ground-truth/B3-STATUS.md`
