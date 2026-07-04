# B3 Answer Key — per-diff SITE + AXIS + BAND (pre-registered)

**Authored:** 2026-07-03, BEFORE any run (D-07/D-11). Extends the S/B-item + expected-band
model of `plugins/vibe-check/docs/efficacy/ANSWER-KEY.md` with an explicit **AXIS** column.
Scoring input: `state.passes[-1].findings[]` from the archived per-run
`runs/<diff-id>/run-<n>/state.json` (D-06 — never the chat transcript).

## Pre-registration

The pre-registration proof (this file's committing-commit hash + the SHA-256 of its
committed blob) is recorded in the SEPARATE manifest
`docs/design/b3-ground-truth/PREREGISTRATION.md`, written in a FOLLOW-UP commit (Task 5)
so this key blob never contains its own hash. Wave 3 recomputes
`git show <the manifest's recorded key commit>:docs/design/b3-ground-truth/ANSWER-KEY-b3.md | shasum -a 256`,
compares it to the manifest's recorded digest, and EXITS NON-ZERO on mismatch; it parses
the SCORED rows FROM that committed blob (never this live file); it requires
`git merge-base --is-ancestor <the recorded key commit> HEAD` to exit 0 and that every
commit touching `docs/design/b3-ground-truth/runs/` descends from that key commit. This
key file therefore carries NO output-dependent and NO self-referential-hash placeholders —
the two proof values live only in PREREGISTRATION.md, filled from git BEFORE any run.

## Preamble rules (locked before any run)

### The three-gate catch rule (D-07 — the A16 fix made mechanical)

A **catch** on a should-catch diff requires ALL THREE, as INDEPENDENT gates:

1. **SITE** — the finding's `file` + `line` land on the correct file, within the planted
   hunk's line range (line ranges below are keyed to the row's base_sha tree WITH the
   patch applied).
2. **AXIS** — the finding's `title` (+ `category` as corroboration) names the defect
   MECHANISM in the row's AXIS column — not merely a defect at the right location.
3. **BAND** — the finding's rendered `band` (read from state; never recomputed —
   `score.py` is the single writer, ROBUST-01) is ≥ the row's expected band floor.
   Band order: critical > warning > medium > low.

Right-site-wrong-axis OR right-axis-below-band = **`detected-below-threshold`** —
reported honestly in the run table, but a **MISS** in the headline number.

Per §A16 (FABLE-REVIEW-FINDINGS.md): the old "one mechanical line" conflated site with
axis — a finding at the right file:line naming the wrong mechanism was implicitly
credited. It is not credited here. And a should-quiet diff is NOT "globally safe" — each
should-quiet row below names the specific AXIS it is safe ON.

### The A8 fold — exemptions are content-justified, never name-justified

Verbatim intent from §A8: an exemption must be justified by **content** (the route/code
genuinely exposes nothing sensitive — e.g. "returns a static liveness bool, touches no
ORM row"), never by **name** — a route named `/health` never downgrades an expected band,
because naming a data-leaking route `/health` would otherwise train the fleet silent.
Applicability check performed at key-authoring time: NO B3 diff in this set contains a
`/health`-style route, so A8 applies as this standing preamble rule rather than any
per-row change. If a future set adds a diff with a `/health`-named route, its row must
state the CONTENT reason silence is correct.

### The FP rule (D-08)

An **FP** on a should-quiet diff = any finding with band **critical or warning** (the
tool's own action bar). **Medium/low** findings on should-quiet diffs are recorded as
noise-notes — counted and reported, but NOT FPs.

### The aggregation rule (D-09 — no rounding)

- Per-run and per-diff fractions are reported.
- Headline **catch-rate** = total catches / total should-catch runs (3 diffs × 3 runs = 9).
- Headline **FP-rate** = FP runs / total should-quiet runs (3 diffs × 3 runs = 9).
- **No rounding:** 2/3 never becomes "caught"; a fraction is reported as the fraction.

### The head check (every scoreable run)

Every Wave-2 run happens on a DETACHED checkout of the row's base_sha with the planted
diff UNCOMMITTED, so HEAD never moves: a scoreable run's `passes[-1].head_sha` MUST equal
the row's base_sha, and `len(passes)` MUST be 1. A run failing either is `unscoreable`
(D-06) — repeated, never guessed.

### Method note (D-13)

Runs measure the SHIPPED DEFAULT config (`codex=auto` — no `--codex` forcing, no toml
overrides beyond what the source repos already have). The per-run Codex outcome line
(joined/skipped) is recorded so the report can state whether Codex contributed;
`attribution: "codex-adversarial"` findings are recorded, not forced (Open Q2).

## Should-catch rows (3 diffs × N=3 runs)

Line ranges are post-image (the patched tree at base_sha). base_sha is BOTH the tree the
SITE line numbers are keyed to AND the exact `head_sha` Wave 3 must find in the run state.

| diff-id | SITE (file : planted-hunk lines) | AXIS (mechanism the finding MUST name) | expected band (floor) | base_sha |
|---|---|---|---|---|
| triggarr-secret-in-logs | `triggarr/clients/base.py` : 230-238 (bug lines 233+235) AND/OR 249-256 (bug lines 252+254) — either hunk satisfies SITE | **Secret/PII (API key) leaked into logs** — `logger.warning(..., exc=exc)` interpolates the full exception (httpx error URL carries the *arr API key; pydantic ValidationError echoes the payload) into log output. NOT "log formatting inconsistency" — a finding at base.py:230 calling it log formatting is right-site-wrong-axis = detected-below-threshold = a MISS. | warning (security) | f4366a261fcf9bab01b48ad89279aac973a7d9b1 |
| triggarr-autoescape | `triggarr/web/routes.py` : 42-48 (bug line 45, the `Jinja2Templates(directory=..., autoescape=True)` call) — hunk 17-22 (the dropped `import jinja2`) is supporting context, not the SITE | **XSS surface re-enabled by losing the preconfigured autoescape `jinja2.Environment`** — on current Starlette, `Jinja2Templates(directory=..., autoescape=True)` silently NO-OPs autoescape (the `**env_options` passthrough was removed), so template auto-escaping is OFF. The finding must name the escaping/XSS consequence (autoescape not in effect / XSS), not merely "refactor reverted" or "unused import". Subtler than a raw `autoescape=False`. | warning (security) | e11187e190b82f281543039e8c3857c6343c54a2 |
| third-organic-should-catch | `src/angular/src/app/services/files/view-file.service.ts` : 304-311 (bug lines 307-309, the unclamped ternary) | **Unclamped percentage — `percentDownloaded` computed as `Math.trunc(100 * local / remote)` with NO upper bound**: extracted files (local unpacked size > remote archive size) render >100% (e.g. "199%") and break the `=== 100` completion state. The finding must name the missing clamp / out-of-range value, not generic style. | medium (correctness; a UI display defect — an honest floor, not the security bar) | 3db8b48bfd20e7ed873343ddc45b7e47d27e3b0e |

## Should-quiet rows (3 diffs × N=3 runs)

Each is a shipped, organic, pure-M FEATURE commit whose selected lines no later commit
rewrote (line-level, subject-agnostic evidence in the `.provenance` sidecars). Per A16,
each is named safe ON a specific axis — not "globally safe". Per D-08, only a
critical/warning finding on these diffs is an FP; medium/low = noise-notes.

| diff-id | SITE (file : feature-hunk lines) | Safe ON axis (A16) | FP rule | base_sha |
|---|---|---|---|---|
| should-quiet-1 | `triggarr/web/validation.py` : 79-91 | SSRF / input-validation: the diff TIGHTENS the host block-list (adds `is_multicast` + IPv4-mapped-IPv6 inspection); backward-compatible, no leak, no injection | any critical/warning = FP | 98eb4196e2c060b38775ab40d6d23e2dc2bee024 |
| should-quiet-2 | `src/angular/src/app/services/utils/rest.service.ts` : 53-63 | API contract / typing: `post(url)` widened to `post(url, body?: object)` passing `body ?? null` — the four existing no-body callers unaffected; pipeline unchanged | any critical/warning = FP | 84aff278f2b735dffef0e91d58bb597b1986caf2 |
| should-quiet-3 | `src/roonseek/transfer.py` : 201-218, 220, 256-257 | HTTP-client / path-injection / error-handling: new `cancel_download` URL-encodes both path segments (`quote(..., safe="")`), `success_statuses` param preserves existing 200/201 default; API key never logged (T-02-03 invariant preserved) | any critical/warning = FP | 10276919fc2f1123cf0d8da7c0d43488087f1bc7 |

## Owner confirmation (D-02)

owner_confirmed: true — the owner confirmed all three should-quiet picks as-is on
2026-07-03 (Task 2b checkpoint, option confirm-all).

One-line-each pick summary as confirmed:

- should-quiet-1 — triggarr `1a8c9f9` "feat(59-02): block IPv4-mapped IPv6 and multicast
  addresses in validate_arr_url" (+6, `validation.py`), base_sha `98eb419...` (= 1a8c9f9^)
- should-quiet-2 — seedsyncarr `3c27e17` "feat(111-02): extend RestService.post with
  optional JSON body" (+3/-2, `rest.service.ts`), base_sha `84aff27...` (= 3c27e17^)
- should-quiet-3 — roonseek `2a6bbd9` "feat(22-03): add slskd transfer cancel boundary"
  (+15, `transfer.py`), base_sha `1027691...` (= 2a6bbd9^)

## D-11 decision-rule table (pre-registered BEFORE any run)

Coarse verdict vocabulary (D-11): **high catch + ~zero FP** → "don't proceed — park the
challenges"; **low catch OR high FP** → "proceed on the implicated challenge(s)";
**middle** → "need more data — grow the committed set next milestone". These rules are
COARSE on purpose: N=3 per diff (9 catch runs, 9 quiet runs) cannot support fine
thresholds, and the Wave-3 report must say so.

| B3-gated challenge | Measured failure mode that implicates it | Coarse verdict trigger |
|---|---|---|
| H-CORE | Misses where the raw agent never emitted the finding at all (truly-silent at the agent, not filtered by the scorer) — evidence that filtering is agent-side in unverified prompt text | Repeated truly-silent misses on should-catch runs → proceed on H-CORE |
| H-DUP | FP or band-crossing driven by a correlated same-model twin pair cross-confirming the same borderline site (+10 rescuing what neither agent alone would surface) | Any should-quiet FP whose surviving band owes its crossing to a same-model cross-confirm → proceed on H-DUP |
| H-LANE | One planted defect double-reported by different lanes (architecture↔impact, bugs↔framework) with no shared attribution — duplicate noise in catch runs | Recurring double-reports of a single planted defect across lanes → proceed on H-LANE |
| B-SEV | `detected-below-threshold` misses caused by band/severity-label instability — right site, right axis, band flapping below the floor across the 3 runs | Right-site-right-axis-below-band misses, esp. with run-to-run band variance → proceed on B-SEV (with B-REWEIGHT) |
| B-XCONF | Catches or FPs whose band crossing depends on the flat +10 cross-confirm regardless of model independence (same-model twin priced equal to cross-model codex) | Band crossings within +10 of the floor attributable to cross-confirm set membership → proceed on B-XCONF |
| B-PROX | SITE-gate or dedup errors caused by the fixed ±2 line radius — co-located distinct findings merged, or the same defect at slightly greater distance not joined | SITE matches/dedups failing on line-radius technicalities in the scored runs → proceed on B-PROX |
| B-REWEIGHT | Unstable per-diff catch fractions (1/3, 2/3) driven by raw agent-confidence swings on the same planted item (the formula's noisiest input) | Per-diff catch fractions between 0/3 and 3/3 with large confidence variance on the same item → proceed on B-REWEIGHT (with B-SEV) |

## Scoring output states (per run, per should-catch diff)

- **catch** — SITE ∧ AXIS ∧ BAND all pass.
- **detected-below-threshold** — SITE passes but AXIS wrong, or SITE ∧ AXIS pass but band
  < floor. A MISS in the headline; reported with the observed title/band.
- **miss** — no finding lands in the planted hunk at all.
- **unscoreable** — state missing/corrupt, `len(passes) != 1`, or `head_sha != base_sha`
  (D-06): repeat the run, never guess.

Per should-quiet diff: **FP** (any critical/warning), **noise-note** (medium/low —
recorded, not counted), **clean** (no findings ≥ medium, or none at all), **unscoreable**
(same D-06 rule).
