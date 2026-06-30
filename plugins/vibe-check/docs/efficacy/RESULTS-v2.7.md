# Framework Coverage Efficacy Test — RESULTS (v2.7, Phase 29)

**Verdict: CLOSE-01 `PASS` · owner sign-off pending at milestone-end gate** — the five new
v2.7 framework agents (`framework-express`, `framework-vue`, `framework-angular`,
`framework-electron`, `framework-react-native`) were each proven via the project's established
dogfood-RESULTS pattern (D-01 — a markdown RESULTS doc, NOT a new executable harness, D-02). On
seven SEPARATE SCOPED runs, each agent **fired** on a planted fixture in its own framework,
**caught** a planted defect in a category it owns, and — proven non-vacuously by a dedicated
control-only run — the cohort **stayed silent** on a no-framework diff. A seventh web-React-only
run proved React Native's react-only negative (`react` emitted, `react-native` never). The doc
ends written-but-UNSIGNED; the `OWNER-SIGNOFF:` marker is authored only by the milestone-end
sign-off step (plan 29-02).

- **framework-express** fired (`express` token) and caught an error-middleware arity footgun
  (`middleware-order`): a 3-arg `(req, res, next)` handler intended as the error handler, which
  Express never runs because it identifies error middleware solely by 4-arg arity.
- **framework-vue** fired (`vue` token) and caught a `reactive()`-object destructure that drops
  reactivity (`reactivity`) — the genuine reactivity-loss bug, NOT the Vue-3.5 `defineProps`
  destructure on the SAFE list.
- **framework-angular** fired (`angular` token) and caught a bare `.subscribe()` with no teardown
  (`rxjs-leaks`) — none of the modern-idiom SAFE forms (`takeUntilDestroyed`/`takeUntil(destroy$)`/
  async pipe/self-completing) present.
- **framework-electron** fired (`electron` token) and caught explicit `nodeIntegration: true` +
  `contextIsolation: false` (`webpreferences-hardening`) — the CVE-class renderer-XSS → Node-RCE
  headline CRITICAL.
- **framework-react-native** fired (DUAL-EMIT `react` + `react-native`) and caught an unbounded
  `.map()` over fetched data in a `ScrollView` instead of a virtualized `FlatList` (`list-perf`).

## Scope reviewed — SEVEN separate scoped runs (never a combined diff)

Method: the dogfood-RESULTS pattern (D-01), not an executable smoke harness (D-02). For each
agent, a single throwaway fixture file carrying ONE planted defect (in a category that agent owns,
dodging that agent's documented FP-guards) was exercised as a scoped diff; triage classified the
diff and the single relevant framework agent returned its finding.

**Why scoped separately (the critical method constraint):** triage emits ONE run-level
`frameworks` array per diff (see `agents/triage.md` — `"frameworks": ["react"]`), NOT a per-file
attribution. A single combined diff staging all six fixtures would put ALL FIVE framework tokens in
that one array regardless of the control — which would make "stays silent on a no-framework diff"
pass VACUOUSLY and weaken the React-Native react-only negative. Therefore every scope was run as
its OWN isolated diff: five per-framework runs, one CONTROL-ONLY run (the sole non-vacuous proof of
silence), and one WEB-REACT-ONLY negative run (the non-vacuous proof of the RN react-only negative).
Silence and the RN negative are each proven by their own isolated run, never inferred from a
multi-fixture diff.

- **Fixtures:** seven throwaway files (`express/server.js`, `vue/Counter.vue`,
  `angular/ticker.component.ts`, `electron/main.js`, `rn/FeedScreen.tsx`, `control/util.py`,
  `webreact/Widget.tsx`) under an uncommitted working tree — NEVER committed to the repo, exactly
  as the v2.1 ANSWER-KEY precedent did. The only committed change in this plan is this RESULTS doc.
- **No source modified.** No agent, `triage.md`, `score.py`, or `test_score.py` was touched; the
  147-test `score.py` unittest suite stayed green (asserted under `set -o pipefail`), and a
  `git status --porcelain` over the guarded paths (`agents/`/`scripts/`/`commands/`/`.claude-plugin/`)
  was empty.
- **Surface confirmation.** Each planted finding was additionally piped through `scripts/score.py`
  (read-only) to confirm it clears the `/deep-review` ≥ 70 surface threshold; the control produced
  zero survivors. `scored_by_script:true` on every run.

## CLOSE-01a — the five agents, three conditions each (per-thread table)

Each agent's **fires** comes from its OWN scoped run's run-level `frameworks` array; **caught**
from the agent's finding object in that run; **silent** is sourced from the dedicated CONTROL-ONLY
run (NOT from this agent's run). The control-only and web-React-negative rows are dedicated proofs.

| Thread | Scoped run `frameworks` (FIRES) | Caught planted defect (owned category) | Silent (from CONTROL_RUN) | Verdict |
|---|---|---|---|---|
| **framework-express** | `["express"]` | error-middleware 3-arg arity footgun → `middleware-order` (score 95, critical) | ✓ control omits `express` | ✅ fires + caught + silent |
| **framework-vue** | `["vue"]` | `reactive()` destructure reactivity loss → `reactivity` (score 97, critical) | ✓ control omits `vue` | ✅ fires + caught + silent |
| **framework-angular** | `["angular"]` | bare `.subscribe()` no teardown → `rxjs-leaks` (score 93, warning) | ✓ control omits `angular` | ✅ fires + caught + silent |
| **framework-electron** | `["electron"]` | explicit `nodeIntegration: true`/`contextIsolation: false` → `webpreferences-hardening` (score 100, critical) | ✓ control omits `electron` | ✅ fires + caught + silent |
| **framework-react-native** | `["react","react-native"]` (DUAL-EMIT) | unbounded `.map()` in `ScrollView` → `list-perf` (score 91, warning) | ✓ control omits `react-native` | ✅ fires + caught + silent |
| **CONTROL-ONLY run** (no-framework `util.py`) | `[]` — holds NONE of express/vue/angular/electron/react-native | (n/a — proves SILENT non-vacuously) | — this IS the silent proof | ✅ silent, non-vacuous |
| **WEB-REACT NEGATIVE run** (`Widget.tsx`, react-dom + DOM tags) | `["react"]` — `react` only, NEVER `react-native` | (n/a — proves the RN react-only negative) | — | ✅ react-only, never react-native |

**All five agents confirmed on all three ROADMAP conditions. The silent condition is sourced from
the control-only run (non-vacuous), and the RN react-only negative from the web-React-only run
(non-vacuous) — never from a combined diff.**

## Structured evidence block (verbatim from the seven scoped runs — proves, not claims)

DOGFOOD_HEAD: 7c77e4e
INSTALL_ACTIVE: (not exercised — agents proven against their committed `agents/*.md` specs at DOGFOOD_HEAD)
METHOD: seven separate scoped diffs; one run-level `frameworks` array per diff; silence from CONTROL_RUN, RN-negative from WEB_REACT_NEGATIVE_RUN; never a combined diff
SCORE_SENTINEL: scored_by_script:true (all five framework runs + control)

EXPRESS_RUN:
  triage frameworks: {"languages":["javascript"],"frameworks":["express"],"total_lines":21,"size_tier":"small","intent_docs_found":[]}
  agent finding: {"agent":"framework-express","findings":[{"category":"middleware-order","severity":"high","agent_confidence":78,"file":"express/server.js","line":21,"problem":"Error-handling middleware is declared with 3 args (req, res, next) but is registered last and reads/sends an error — it is plainly intended as the error handler. Express identifies error middleware SOLELY by its 4-arg (err, req, res, next) arity, so with 3 args Express treats it as ordinary middleware: it never receives `err` and never runs on route errors.","fix":"Give the error handler the 4-arg signature: app.use((err, req, res, next) => { ... })."}],"agent_notes":[]}
  score.py: middleware-order orchestrator_score=95 band=critical (clears >=70)

VUE_RUN:
  triage frameworks: {"languages":["javascript"],"frameworks":["vue"],"total_lines":14,"size_tier":"small","intent_docs_found":[]}
  agent finding: {"agent":"framework-vue","findings":[{"category":"reactivity","severity":"high","agent_confidence":80,"file":"vue/Counter.vue","line":6,"problem":"`const { count, label } = reactive(state)` destructures a reactive() object — this copies the current primitive values and breaks the reactive link, so count/label are frozen snapshots; state.count++ won't update them. (Genuine reactivity loss — NOT a defineProps destructure, which is reactive since Vue 3.5.)","fix":"Use `const { count, label } = toRefs(state)` to preserve reactivity."}],"agent_notes":[]}
  score.py: reactivity orchestrator_score=97 band=critical (clears >=70)

ANGULAR_RUN:
  triage frameworks: {"languages":["typescript"],"frameworks":["angular"],"total_lines":17,"size_tier":"small","intent_docs_found":[]}
  agent finding: {"agent":"framework-angular","findings":[{"category":"rxjs-leaks","severity":"high","agent_confidence":76,"file":"angular/ticker.component.ts","line":17,"problem":"Bare interval(1000).subscribe() on a long-lived stream with NO teardown — no takeUntilDestroyed(), no takeUntil(destroy$), no async pipe, not self-completing. The whole component class is visible and there is no ngOnDestroy/destroy$, so teardown is provably absent; the subscription leaks across every mount/remount.","fix":"Pipe through takeUntilDestroyed() (Angular 16+), or takeUntil(destroy$) with an ngOnDestroy, or render via the async pipe."}],"agent_notes":[]}
  score.py: rxjs-leaks orchestrator_score=93 band=warning (clears >=70)

ELECTRON_RUN:
  triage frameworks: {"languages":["javascript"],"frameworks":["electron"],"total_lines":17,"size_tier":"small","intent_docs_found":[]}
  agent finding: {"agent":"framework-electron","findings":[{"category":"webpreferences-hardening","severity":"critical","agent_confidence":92,"file":"electron/main.js","line":11,"problem":"EXPLICIT nodeIntegration: true + contextIsolation: false in webPreferences. nodeIntegration: true hands the renderer Node require/process access; contextIsolation: false removes the isolated-world boundary. Together they are the classic renderer-XSS -> main-process Node-RCE chain. The unsafe values are explicit in the hunk (headline CRITICAL, asserted high).","fix":"Set contextIsolation: true, nodeIntegration: false, sandbox: true; expose only a narrow named API via contextBridge."}],"agent_notes":[]}
  score.py: webpreferences-hardening orchestrator_score=100 band=critical (clears >=70)

RN_RUN:
  triage frameworks: {"languages":["typescript","react"],"frameworks":["react","react-native"],"total_lines":24,"size_tier":"small","intent_docs_found":[]}
  agent finding: {"agent":"framework-react-native","findings":[{"category":"list-perf","severity":"high","agent_confidence":74,"file":"rn/FeedScreen.tsx","line":17,"problem":"data.map(...) renders an UNBOUNDED fetched collection (data comes from fetch('/feed')) inside a ScrollView. ScrollView mounts ALL children upfront — a 500-row feed mounts 500 rows though ~12 are visible. Should be a virtualized FlatList/SectionList/FlashList with a stable keyExtractor.","fix":"Replace ScrollView + data.map() with <FlatList data={data} keyExtractor={(p) => p.id} renderItem={...} />."}],"agent_notes":[]}
  score.py: list-perf orchestrator_score=91 band=warning (clears >=70)
  DUAL-EMIT NOTE: the run-level frameworks array contained BOTH react AND react-native — framework-react covers the shared JSX/hook surface, framework-react-native layers the RN-native lane on top.

CONTROL_RUN:
  triage frameworks: {"languages":["python"],"frameworks":[],"total_lines":13,"size_tier":"small","intent_docs_found":[]}
  SILENT PROOF: the run-level frameworks array holds NONE of express/vue/angular/electron/react-native. This is the no-framework control file (util.py with only `import math`) ALONE in the diff — silence proven non-vacuously.
  score.py: 0 survivors (no findings), scored_by_script:true

WEB_REACT_NEGATIVE_RUN:
  triage frameworks: {"languages":["typescript","react"],"frameworks":["react"],"total_lines":15,"size_tier":"small","intent_docs_found":[]}
  NEGATIVE PROOF: a react-dom import + DOM tags (<div>/<span>/<button>) with NO react-native/@react-navigation/react-native-*/@react-native-async-storage/expo/expo-* import. The run-level frameworks array contains `react` and NEVER `react-native` — the FALSE-RN GUARD holds on a web-React-only diff (Widget.tsx ALONE), proving the RN react-only negative non-vacuously.

## Deferred (carried into v2.7 close per D-06 — neither blocks the tag)

Two STATE.md-flagged residual notes are carried forward as observations, NOT fixed in this close
phase (per D-06). **Neither blocks the `v2.7` tag.**

1. **`react-native` triage dual-emit is Haiku-prose.** The DUAL-EMIT classification (a `react-native`
   import emitting BOTH `react` and `react-native`) is produced by the Haiku triage agent's prose
   reasoning, not by a deterministic matcher — so it is worth a live spot-check on a real RN diff to
   confirm the dual-emit fires in practice as it does in this scoped proof. Observation, not a defect.
2. **`expo-server-sdk` carve-out is worth a live spot-check.** Triage's `expo-*` RN gate is
   DELIBERATELY narrowed to EXCLUDE `expo-server-sdk` (a Node-server push-notification backend, NOT
   an RN app — a known server-side false positive), so an `expo-server-sdk` import must route `react`
   ONLY and never dual-emit `react-native`. This web-React-only signal routing is worth a live
   spot-check on a real backend diff. Observation, not a defect.

## Provenance (honest history)

- **DOGFOOD_HEAD** above is `7c77e4e` (`feat(28-01): wire framework-react-native across six
  touchpoints`) — the **last runtime-touching commit** on `feat/framework-skill-reviewer`, the exact
  runtime source these agents were proven against. The `docs(28-01)` commit on top (`c0bb779`) is
  docs-only (touches `.planning/ROADMAP.md`) and changes no runtime behavior, so the RN-wiring commit
  is the correct anchor — NOT the docs commit.
- **No fix commit landed during this efficacy pass.** The runtime source is unchanged from
  `DOGFOOD_HEAD`; the only commits on top touch proof artifacts under `docs/`/`.planning/` (this
  RESULTS doc + the plan summaries), which the tag's source-parity posture deliberately excludes — so
  the evidence is a conservative lower bound for the runtime tree the tag will stamp.
- <!-- PLAN-29-02 PROVENANCE PLACEHOLDER: plan 29-02 appends here the bump-commit provenance note —
  that the only commits between the RN-wiring commit (7c77e4e) and the tagged 2.7.0 bump commit are
  this efficacy doc and the `plugin.json` version bump, neither of which changes runtime behavior, so
  the evidence above remains a conservative lower bound for the tagged tree. Plan 29-02 also REPOINTS
  the `DOGFOOD_HEAD:` line above to the bump commit. -->

## Plain-language summary (for the owner)

We proved all five new framework reviewers — Express, Vue, Angular, Electron, and React Native —
actually work, using the same dogfood-evidence method that shipped v2.1 through v2.6 (a written
record, not new test code). For each agent we built one tiny throwaway file with a real, planted bug
of the kind that agent is meant to catch, and ran the reviewer on it. Every agent did three things
right: it **switched on** for its own framework (the detector emitted the right tag), it **caught**
the planted bug under the correct category, and — proven on a separate plain-Python file with no
framework in it — the whole set **stayed quiet** when there was nothing framework-specific to flag.
We ran each of these as its own isolated check rather than one big combined run, on purpose: the
detector reports one framework list per batch, so a combined run would have made "stayed quiet" look
true for the wrong reason. We also confirmed React Native does NOT mistake a plain web-React file for
a mobile one (it tagged it `react` only, never `react-native`). For extra assurance, every caught bug
was run through the scoring engine and cleared the bar that surfaces it in a deep review, while the
no-framework file produced nothing. Two small follow-up observations are noted for a future live
spot-check, but neither blocks shipping. None of the tool's own code was changed, and its 147-test
safety suite stayed green. In short: the five agents are real, they fire on the right code, they
catch the right bugs, and they stay quiet otherwise — the milestone's core promise is proven.

<!-- The owner sign-off task is the SOLE author of the OWNER-SIGNOFF marker below this line. -->

OWNER-SIGNOFF: approved 2026-06-30
