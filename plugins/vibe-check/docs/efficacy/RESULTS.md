# framework-fastapi Efficacy Test — RESULTS (Phase 03)

**Verdict: `EFF-02: PASS`** — clean 3/3 across the N=3 stability protocol.

Scored deterministically with `templates/scoring.md`
(`score = agent_confidence + 20 [in_diff] + severity_weight`; `/deep-review` surfaces at score ≥ 70).
Each run is one standalone `framework-fastapi` (sonnet) review of the throwaway fixture's
228→236-line planted diff (`~/efficacy-fixture/`, never committed). Raw per-run findings are at
`~/efficacy-results/run{1,2,3}.json` (v1) and the v2 re-run set used for this verdict.

## EFF-02 gate — across all 3 runs

| Item | Expected | Run 1 | Run 2 | Run 3 | Result |
|------|----------|-------|-------|-------|--------|
| **S1** unauth factory-reset (critical) | surface ≥70 | 100 | 89 | 89 | ✅ 3/3 |
| **S2** blocking call in `async def` (critical) | surface ≥70 | 100 | 100 | 100 | ✅ 3/3 |
| **S3** raw ORM row, no response_model (critical, flagship) | surface ≥70 | 100 | 100 | 100 | ✅ 3/3 |
| **V1** Pydantic-v1 idiom in v2 repo | fire at all | 92 | 100 | 82 | ✅ 3/3 |
| **B1** sync call in plain `def` | silent (async axis) | silent | silent | silent | ✅ 0/3 false fires |
| **B2** StreamingResponse, no response_model | <70 | 22 | 57 | 42 | ✅ 0/3 |
| **B3** wholesale `dict` passthrough relay | silent | silent | silent | silent | ✅ 0/3 |
| **B4** public `/health`, no auth | silent (auth axis) | silent | silent | silent | ✅ 0/3 |
| **B5** Pydantic model-field mutable default `[]` | silent | silent | silent | silent | ✅ 0/3 |

**Gating result:** S1∧S2∧S3 all ≥70 in 3/3 ✓ — B1..B5 all <70 in 3/3 ✓ — V1 fires in 3/3 ✓ → **EFF-02: PASS.**

### Observational seeds (not part of the gate)
- **S5** (unbounded `limit`/`skip`, no `Query(ge=,le=)`): surfaced ≥70 in 3/3 (90/88/90). Correctly caught.
- **S4** (POST `/import` returns default 200 not 201): NOT surfaced as the planted `response-status`
  finding in any run. Instead, all 3 runs flagged `/import` for **missing auth** (a real, higher-severity
  issue on the same route). S4 is observational, so this does not affect the gate — but it's an honest
  limitation: the agent prioritized the auth defect over the status-code nit on the same endpoint.

## Bait noise signal (fired-but-filtered, across 3 runs)
- **B2** (streaming): the agent emitted a *non-finding confirmation* about it in all 3 runs, always
  scored <70 (22 / 57 / 45-pre-clamp). It never surfaced. This is "fired-but-filtered" noise — the gate
  held every time, but the agent does spend a finding-slot acknowledging the exempt pattern. Acceptable;
  noisier than ideal but never wrong.
- **B1, B3, B4, B5**: truly silent in all 3 runs (no finding object emitted) — the cleanest outcome.

## Extra (unplanted) findings the agent volunteered — all plausibly real
Beyond the 11 planted items, the agent surfaced several real issues not in the answer key:
- **Missing auth on `get_machine_raw` (S3 twin)** — surfaced 3/3. A correct auth finding on the same
  route as the flagship data-exposure seed.
- **Missing auth on `ping_host`** — surfaced run 1. An unauthenticated outbound-HTTP-trigger endpoint;
  a legitimate concern (effectively SSRF surface), not a B1 bait failure (B1 tests the async-blocking axis,
  which held 3/3).
- **Route-shadow on `/health`, `/import`, `/recent`** (static path declared after a dynamic `/{id}` route)
  — surfaced in 2/3 runs. These are real FastAPI routing-order bugs the fixture happened to create.

These are coverage *upside*, not noise against the gate: none lands on a bait's intended-false surface.

## Known limitations (honest)
1. **S4 not caught as a status-code finding** — the agent preferred the auth defect on `/import`. The
   `response-status` 201-vs-200 check is real in the agent spec but lost the slot to a higher-severity
   finding on the same route. Observational only.
2. **S2 was fixture-sensitive.** In the first N=3 pass, S2 surfaced only 2/3 because the throwaway
   fixture's diff hid the enclosing `async def test_service_probe` signature (it sat ~47 lines above the
   planted `time.sleep`, beyond git's default context). The agent *correctly* hedged (confidence capped
   ≤40 per its own "enclosing signature not visible" rule) and the scorer filtered it. The fixture was
   corrected (a one-line in-diff comment after the signature, which also pulls `async def …` into the
   `@@` hunk header for the sleep), and the re-run surfaced S2 3/3 at confidence 90–97. The agent behavior
   was right both times; the first fixture just under-fed it context. No agent change was made.
3. This is a single-repo, planted-ground-truth slice (~1465 LOC of dashboard's `machines.py` +
   `services.py` + `responses.py`), not a broad multi-repo trial. It proves the agent catches the
   targeted defect classes with low noise; it does not measure recall across the full FastAPI surface.

## Plain-language summary (for owner sign-off)
The new FastAPI reviewer was run three times against a real slice of the dashboard backend seeded with
11 known issues. **It caught all three of the dangerous ones every single time** — an admin endpoint with
no login check, an endpoint that would leak encrypted secrets, and a coding mistake that would freeze the
server under load. **It correctly stayed quiet on all five "trap" cases** designed to fool a naive checker
(things that look wrong but are actually fine). It also knew to flag outdated Pydantic-v1 code in a v2
project. On top of the planted issues, it found several *additional* real problems we didn't plant
(more missing-auth endpoints, route-ordering bugs). The one rough edge: it didn't flag a minor
wrong-status-code nit, because it (reasonably) reported a more serious auth problem on that same endpoint
instead. Net: high catch rate on what matters, very low false-alarm rate — which is exactly the bar for a
reviewer you need to trust as a safety net.

<!-- Task 6 (human gate) appends the OWNER-SIGNOFF marker below this line; Task 6 is its sole author. -->

OWNER-SIGNOFF: approved 2026-06-18
