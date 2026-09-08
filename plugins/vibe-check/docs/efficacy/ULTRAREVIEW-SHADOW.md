# Ultrareview shadow pass — capture template

> **Status:** SCAFFOLDING ONLY — no runs recorded. Backlog **999.18**.
> **Do not run this while a measured baseline window is open.** As of 2026-09-08 the
> v2.10 Phase-38 baseline is COMPLETE (36/36 runs committed), so a no-baseline gap is open
> until Phase 43's re-measure begins; this pass competes for the same owner-run budget, so
> run it in that gap or after Phase 44 ships — never while Phase 43 runs are in flight.

## What this is

A **gap analysis**, not a benchmark. It points Anthropic's `/code-review ultra` at diffs
from the committed B3 ground-truth set and asks one question:

> **Which classes of finding does a strong generalist reviewer surface here that
> vibe-check's specialist fleet structurally cannot reach?**

The output is a bucketed table that feeds the backlog — new agents, new lanes, new
never-flag classes, or answer-key corrections.

## What this is explicitly NOT

**Not a catch-rate / FP-rate comparison.** Do not publish a precision-recall table for
ultrareview next to vibe-check's. The realistic sample here is ~1 run per diff on 2-4
diffs; the vibe-check numbers are ×3 across 12 diffs. The error bars would swamp any
difference, and a number with n=2 invites exactly the over-reading the B3 pre-registration
discipline exists to prevent. If a rate is computed anyway it MUST carry its n and CI.

**Not a like-for-like matchup.** `/code-review ultra` is a general-purpose branch/PR
reviewer. vibe-check fans out 12+ language/framework specialists with a confidence axis,
severity banding, and noise ceilings. On `triggarr-autoescape` (a Jinja2 XSS surface) a
generalist miss measures generalist-vs-specialist, not reviewer quality. State this
before any table in the write-up.

**Not automatable.** `/code-review ultra` is user-triggered and billed. The assistant
cannot invoke it via Bash or otherwise. Every arm is a manual owner invocation plus a
manual capture paste.

## Cheapest honest version

**2 diffs × 1 run = 2 owner invocations.**

Reuse the two diffs the Phase-40/41 spot-checks already use, so the vibe-check side is
already recorded and needs no new runs:

| role | diff | repo | base_sha |
|---|---|---|---|
| should-catch | `triggarr-secret-in-logs.patch` | `~/triggarr` | `f4366a2` |
| should-quiet | `should-quiet-1.patch` | `~/triggarr` | `98eb419` |

Expand to 4 diffs only if the first pass lands bucket (b) or (c) hits.

## Procedure (per diff)

The setup mirrors the B3 run-checklist so the reviewed tree is byte-identical to what
vibe-check saw — that is the whole point of reusing the kit.

1. **Never run this in a source clone that is mid-B3-run.** Check for
   `.turingmind/state/.b3-inprogress` first; if present, stop.
2. Detach the source clone at the diff's `base_sha` and apply the patch, exactly as
   `RUN-CHECKLIST-v2.10.md` does. Verify the live full-diff sha256 matches the sealed
   `EXPECTED_TREE_DIFF_SHA256` in the diff's `.provenance` sidecar.
3. Record the harness fingerprint (Claude Code version, model, date) the same way STEP
   0.25 does — an ultrareview run is still a measured observation.
4. Owner runs `/code-review ultra` in that clone. Capture the complete finding list
   verbatim into `runs-ultrareview/<diff-id>/findings.md`.
5. Revert the clone (the checklist's revert-once block).

## Adjudication buckets

Score each ultrareview finding against the SAME sealed answer key the vibe-check runs are
scored against — routing by diff origin, exactly as `SCORING-v2.10.md` does across the
two-seal split:

- **Carried v2.9 diffs** (including both diffs recommended above, `triggarr-secret-in-logs`
  and `should-quiet-1`) → the v2.9 blob, `docs/design/b3-ground-truth/ANSWER-KEY-b3.md` @
  `ef0ab67`.
- **New v2.10 diffs** → `docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md` @ `5f687d9`.
  That blob holds rows for the six NEW diffs only; carried diffs have no rows in it.

Do not create a new key — reusing the sealed ones is what makes this cheap and honest.
Reading the wrong blob for a diff yields zero matching rows and would push every real
finding into bucket (c) spuriously.

| bucket | meaning | what it implies |
|---|---|---|
| **(a) shared** | in the key, vibe-check also caught it | no signal — expected overlap |
| **(b) gap** | in the key, vibe-check MISSED it | a real recall gap; candidate agent/lane work |
| **(c) key-expansion** | a real defect NOT in the sealed key | **highest value** — the keys are under-specified, which affects EVERY past and future measurement |
| **(d) false alarm** | not a real defect | ultrareview noise; interesting only in bulk |

**Bucket (c) is the reason to do this at all.** A real defect that neither the key nor
vibe-check names means the ground truth itself has a hole. That finding is worth more
than any score, and it retroactively qualifies the v2.9 catch-rate of 8/9.

> Sealed-key handling: bucket (c) hits do NOT get silently added to the key. The
> pre-registration immutability rule holds. Log them here; a key amendment is a separate,
> explicitly-ordered manifest commit with its own rationale.

## Precedent

v2.5 Phase 21 ([[v2.5-phase21-shipped]]): the test-sufficiency agent's own deep-review
found 2 Critical + 4 Warning defects that plan-review could not reach **by construction**.
The structural-gap finding drove real work; no score was involved. Same shape here.

## Results

_None recorded. Fill in per run._

### Run log

| date | diff | harness fingerprint | findings | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

### Gap table

_Per bucket-(b) and bucket-(c) finding: what class is it, and does vibe-check have a lane
that could have caught it? If yes, why didn't it fire? If no, what would that lane be?_

### Backlog items generated

_None yet._
