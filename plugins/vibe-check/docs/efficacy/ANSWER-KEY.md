# framework-fastapi Efficacy Test — ANSWER KEY (Phase 03)

**Ground-truth map of the 11 planted items** in the throwaway efficacy fixture, scored
against the `framework-fastapi` agent (authored Phase 1, wired Phase 2) via `/deep-review`.

- **Fixture:** a throwaway git repo (`~/efficacy-fixture/`, NEVER committed) holding a
  pristine copy of dashboard's real slice (`machines.py` 660 LOC + `services.py` 728 LOC +
  `responses.py` 77 LOC = 1465 LOC, Pydantic **v2** confirmed, **zero auth** in the slice)
  with the 11 items below injected as **uncommitted** working-tree edits.
- **Line numbers** below are the items' positions **in the fixture working tree** (post-injection),
  re-verified against the live dashboard slice at execution time (paths/LOC/v2/no-auth all held).

## EFF-02 PASS GATE (the one mechanical line)

**EFF-02 PASS = (S1, S2, S3 all surface at score >= 70) AND (B1-B5 all stay < 70) AND (V1 fires at all).**
S4 and S5 are **OBSERVATIONAL seeds** — expected to surface but **NOT part of the gate**.
The verdict is decided on **CONSISTENCY across N=3 stability runs** (3/3); a flaky 2/3 is NOT an
auto-pass — it is analyzed and routed to the Task 8 / D-12 contingency.

## Scoring math (from `templates/scoring.md`, used for the expected-band column)

`score = agent_confidence + 20 (in_diff, true for EVERY planted item) + severity_weight`
where severity_weight = critical +0 | high −3 | medium −8 | low −20. `/deep-review` surfaces
score **>= 70**. Therefore the surface floors are: **high** needs conf >= 53; **medium** needs
conf >= 58; **low** needs conf >= 70; **critical** needs conf >= 50. (+10 cross-confirm with
`security` may apply to S1/S3 — only helps them surface; never assumed in the floor.)

## The 11 planted items

| ID | File:line (fixture) | Category | Planted intent | Expected behavior | Expected band (/deep-review) | Gating role | D-gate / EFF ref |
|----|---------------------|----------|----------------|-------------------|------------------------------|-------------|------------------|
| **S1** | machines.py:681 `factory_reset_machine` (paired with auth on machines.py:94 `create_machine` + :296 `update_machine`, dep at :83 `require_auth`) | auth-security | A NEW state-changing `POST /{machine_id}/factory-reset` that OMITS `Depends(require_auth)` while its siblings carry it. The slice has zero native auth, so the sibling contrast is **manufactured** (Pitfall 1). | **fire-high** | Medium→Critical (conf >= 53 → score >= 70; cross-confirm w/ security likely +10) | **GATING (critical)** | EFF-02; agent §auth-security `[high]` (floor conf >= 53 when route+sibling visible) |
| **S2** | services.py:381 `time.sleep(2)` inside async `test_service_probe` (async def at :333) | async-blocking | A sync blocking call (`time.sleep(2)`) inside an `async def` route — stalls the event loop; should be `run_in_threadpool`. | **fire-high** | Warning/Critical (enclosing `async def` in-hunk → natural high conf, no ≤40 ceiling) | **GATING (critical)** | EFF-02; agent §async-blocking `[high]` (flag ONLY inside async def) |
| **S3** | machines.py:698 `get_machine_raw` (`GET /{machine_id}/raw`) | data-exposure | Returns the raw `Machine` ORM row directly with **NO `response_model=`** and no output schema — leaks `agent_secret_encrypted`, `ssh_password_encrypted`, etc. **FLAGSHIP** catch. | **fire-high** | Warning/Critical (in-hunk row return → natural high conf; cross-confirm w/ security likely +10) | **GATING (critical)** | EFF-02 (flagship); agent §data-exposure `[high]` |
| **S4** | machines.py:709 `import_machine` (`POST /import`) | response-status | A POST that creates a resource but returns default **200** instead of `status_code=201`. | fire-low/medium | Medium or Filtered (low/medium severity; non-critical — band tolerated) | **OBSERVATIONAL** (not gating) | agent §response-status; D-05 (only the 3 criticals gate) |
| **S5** | services.py:767 `list_recent_services` (`limit`/`skip` unbounded, `GET /recent`) | pydantic-validation | `limit: int = 0` / `skip: int = 0` query params feeding the query with **no `Query(..., ge=, le=)`** bounds — unbounded pagination. | fire-low/medium | Medium or Filtered (medium needs conf >= 58) | **OBSERVATIONAL** (not gating) | agent §pydantic-validation `[medium]`; D-05 |
| **B1** | machines.py:722 `ping_host` (`GET /{machine_id}/ping-host`, plain `def`) | async-blocking | A sync `time.sleep(1)` + `requests.get(...)` inside a **plain `def`** route — FastAPI runs plain-def in a threadpool, so this is **NOT a bug**. | **silent** | (no finding >= 70) | **GATING bait** | D-07 gate (flag only inside `async def`) |
| **B2** | services.py:738 `preview_service_logs` (`GET /{service_id}/preview`) | data-exposure | A **newly added** route returning a `StreamingResponse` subclass with **no `response_model`** — a legitimate response_model exemption. Planted as a NEW in-diff route (NOT the pre-existing committed `get_service_icon`, which is never in the diff so its silence can't be tested — NEW-B-01). | **silent** | (no finding >= 70) | **GATING bait** | D-08 exemption (`Response`/`StreamingResponse` subclass exempt) |
| **B3** | services.py:757 `relay_event` (`POST /relay`, `body: dict`) | pydantic-validation | A wholesale `dict` body forwarded as-is with **no key access** — an intentional passthrough relay, not a validation gap. | **silent** | (no finding >= 70) | **GATING bait** | D-11 gate (dict/Any passthrough with no key access = intentional) |
| **B4** | machines.py:735 `machines_health` (`GET /health`) | auth-security | A public `/health`-style GET with no auth — an auth-exemption, not a missing-auth defect. | **silent** | (no finding >= 70) | **GATING bait** | D-09 auth-exemption list (`/health`/`/healthz`/`/metrics`) |
| **B5** | responses.py:88 `DiagnosticsResponse.warnings: list[str] = []` | pydantic-validation | A Pydantic model **FIELD** with a mutable default `= []` — Pydantic deep-copies field defaults per-instance, so this is **SAFE** (the #1 false positive a Python model tempts). | **silent** | (no finding >= 70) | **GATING bait** | D-11 SAFE rule (model-field mutable default is safe; only function-arg defaults are the bug) |
| **V1** | responses.py:94 `@validator("checked_at")` + responses.py:101 `self.dict()` (in `DiagnosticsResponse`) | pydantic-validation | A **genuine Pydantic v1 idiom** (`@validator` + `.dict()`) in a confirmed-v2 codebase — deprecated; the agent SHOULD flag it (low severity), proving version-awareness. NOT `@field_validator` (the v2 idiom already in the slice). | **fire** (must NOT be silent) | Medium (low sev, conf ~70 → score ~70) — but see pass rule below | **GATING (version-aware TP)** | D-07; agent §pydantic-validation `[low]` (v1 idiom in detected-v2 repo) |

**Item count: 11 distinct IDs (S1–S5, B1–B5, V1), one expected-behavior label each. No duplicates, no extras.**

## Bait pass states (Pitfall 3 — three distinguished states, not two)

For each bait B1–B5 the expected behavior is `silent`, but the run analysis (Task 5) must record,
**per run**, which of these occurred:

- **truly-silent** — the agent emitted NO finding object for the bait (the gate fired at the agent). **Full pass.**
- **fired-but-filtered** — the agent emitted a finding the orchestrator scored < 70 (the gate leaked at the agent but the scorer held). **Pass-with-note** (noisier than ideal, but the gate held).
- **surfaced (>= 70)** — the agent emitted a finding that cleared the threshold. **Hard FAIL** for that bait.

**Source of the silent-vs-fired-but-filtered distinction:** the `/deep-review` transcript only shows a
Filtered **count**, which cannot separate "agent silent" from "agent fired-but-filtered" (B-02 / N-02).
That distinction is read from the **per-run raw-findings JSON diagnostics** — one standalone
`framework-fastapi` Sonnet Task paired with EACH of the 3 stability runs
(`~/efficacy-raw-findings-{1,2,3}.json`). The owner-facing noise COUNT is computed **ACROSS ALL 3 RUNS**
("fired-but-filtered in K of 3 runs"), never from a single diagnostic. The D-06 mechanical pass bar is
unchanged: a bait passes as long as it stays < 70 in every run, whether silent or filtered.

## V1 pass rule (M-04 — "fires at all", band-tolerant)

V1 **PASSES iff it fires at all** — surfaced (any band) OR fired-but-filtered at low/medium **citing the
v1 idiom**. The point is proving **version-awareness**, not a precise band: "fired Filtered-low instead of
Medium" is NOT a fail. Record the exact observed band, but judge V1 only on whether the agent
acknowledged the deprecated v1 idiom at all. V1 is the only "must-fire" item among the non-S1/S2/S3 set.

## Cross-confirm note (§Q6)

S1 (missing auth → broken access control) and S3 (raw ORM row → data exposure) overlap the `security`
agent's lane. The framework-fastapi agent flags them with its `auth-security` / `data-exposure`
categories, which map to the **`security` domain** in `scripts/score.py`'s `CATEGORY_DOMAIN`. When a
co-located native `security` finding sits at the same `(file, line ±2)` site, the two **cross-confirm on
category-domain overlap** and EARN the **+10** (orchestrator dedups by `(file, line ±2)` + category-domain
overlap — **NOT** title phrasing, per ROBUST-02 / v2.4). So S1/S3 may score +10 higher than the floor —
this only helps them surface and is recorded, not required. (Historical note: through v2.3 this +10 keyed
on a shared title substring; ROBUST-02 replaced that gameable signal with category-domain overlap, so a
shared title token no longer fires anything — location accuracy and category domain are what matter now.)

## get_service_icon note (NEW-B-01)

The pre-existing `services.py:467 get_service_icon` returns a `Response` (binary icon) with no
`response_model` — a naturally-occurring response_model exemption the agent should also stay silent on.
It is **committed/pristine** (NOT in `git diff HEAD`), so the agent never reviews it as in-diff surface and
its silence is NOT testable. **The tested B2 bait is the NEW `/preview` route at services.py:738, NOT
get_service_icon.**
