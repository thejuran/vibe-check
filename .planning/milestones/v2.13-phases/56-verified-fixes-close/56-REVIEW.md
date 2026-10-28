---
phase: 56-verified-fixes-close
reviewed: 2026-10-23T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - plugins/vibe-check/phases/review/05-state.md
  - plugins/vibe-check/phases/review/20-dispatch.md
  - plugins/vibe-check/phases/review/30-collect-score.md
  - plugins/vibe-check/phases/review/40-render.md
  - plugins/vibe-check/phases/shared/90-finalize.md
  - plugins/vibe-check/scripts/carry_state.py
  - plugins/vibe-check/scripts/fixtures/future-schema.json
  - plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json
  - plugins/vibe-check/scripts/score.py
  - plugins/vibe-check/scripts/test_carry_state.py
  - plugins/vibe-check/scripts/test_confirmed_fix.py
  - plugins/vibe-check/scripts/test_state_shape.py
  - plugins/vibe-check/scripts/test_verified_fixes.py
  - plugins/vibe-check/templates/output-format.md
  - plugins/vibe-check/templates/review-md-schema.md
findings:
  critical: 2
  warning: 6
  info: 3
  total: 11
status: issues_found
---

# Phase 56: Code Review Report

**Reviewed:** 2026-10-23
**Depth:** standard (diff 8df9545..HEAD, with the callers of the changed score.py and carry_state.py code)
**Files Reviewed:** 15
**Status:** issues_found

## Summary

The phase adds two new ways to close a finding: an independent re-check (a non-originating reviewer closes a lead when the blob it judged equals HEAD's blob) and a bound plain re-check for `persisted` records. It also adds a "still applies" memory, `recheck_settled`. The blob binding itself holds. A changed blob, a null snapshot and a null HEAD blob all keep the finding open, and the 399 phase tests pass.

The "still applies" memory does not hold, though. Two separate defects let a finding that a reviewer said still applies close later on byte-identical code. Both were reproduced against the current `score.py`. Separately, the scorer enforces the "never `fix`, never Codex" rule only on some request shapes, and it ignores a still-applies answer given on another route. The new code also adds a crash on malformed carry-forward input that the previous version tolerated, and `applied` fix verdicts are never pruned from state.

Convention pack (`verify conventions --check`): no findings.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A still-applies memory is lost on every kept-open (sub-threshold) row, so the finding can close on unchanged code next run

**File:** `plugins/vibe-check/scripts/score.py:2016` (written onto `rep`), `plugins/vibe-check/scripts/score.py:383` (`_kept_open_rows` rebuilds the row from `entry["record"]`, the raw carried `cf`)
**Issue:** `_judge` writes `record["recheck_settled"]` onto the working copy `rep`. When the carried row then falls below the threshold, `_kept_open_rows` re-emits it from `carried_obligations[id(rep)]["record"]`, which is the original `cf` dict and not `rep`. So:
- (a) the newly recorded memory is dropped from the output row and never reaches state, and
- (b) a memory that the fresh-start rule deliberately deleted from `rep` (line 2111) is resurrected from `cf`.

`needs-recheck` rows get no +15, so they are the rows most likely to be kept-open. They are also the rows that need no trigger to close.

Reproduced with the `test_verified_fixes` helpers:
- Pass 2: a `needs-recheck` test-sufficiency row gets an independent request. `bugs` answers `still-applies`, and the scorer rejects with `fix not confirmed: the routed reviewer says it still applies`. The output row has **no** `recheck_settled` (it went out with `kept_open: sub-threshold`).
- Pass 3: the blobs are identical and `touched_paths` is `{}`. A `resolved` from `bugs` closes the row as `Closed — fix confirmed by the bugs lane`. This is exactly the false closure the D-08 safeguard is meant to prevent.

The same row with status `persisted` (above threshold) keeps the memory correctly. That is why `test_still_applies_keeps_open_and_settles` passes and the gap is not covered.
**Fix:** Carry the guard's output onto the kept-open row. In `_kept_open_rows`, after building `row` from `entry["record"]`, overwrite the memory from the working record:
```python
row.pop("recheck_settled", None)
if isinstance(m.get("recheck_settled"), dict):
    row["recheck_settled"] = m["recheck_settled"]
```
Add a test where the settled row is `needs-recheck` and sub-threshold, with a third pass that sends `resolved` on unchanged blobs. It must stay open with `_R_IR_SETTLED`.

### CR-02: Any commit anywhere in the repo clears the still-applies memory, so a re-asked reviewer can close a finding whose code never changed

**File:** `plugins/vibe-check/scripts/score.py:2100-2111`; prose `plugins/vibe-check/phases/review/05-state.md` (`$TOUCHED_PATHS`)
**Issue:** The fresh-start rule deletes `recheck_settled` when `touched` is non-empty. The code comment says "no commit touching the lead's paths since". But `05-state.md` defines `$TOUCHED_PATHS` as the full output of `git diff --name-only "<anchor>..HEAD"`, with no path filter ("Forward the whole filtered list for the row"). For a settled row the anchor is the settled `head_sha`, so a commit to `docs/README.md` clears the memory. The `20-dispatch.md` skip rule ("its `$TOUCHED_PATHS` list is empty") re-issues the block for the same reason.

Reproduced: a settled `needs-recheck` row with unchanged fingerprint blobs and `touched = {hash: ["docs/README.md"]}`, plus a `resolved` from `bugs`, closes with no rejection. With `touched = {}` it correctly stays open with `_R_IR_SETTLED`. So "a still-applies verdict keeps a finding open until its fingerprint changes" fails on essentially every run that reviews new commits.

For `persisted` rows the effect is softer: the trigger rejects, but the row's rendered reason flips from "Still applies per a reviewer…" to "no change near the finding…".
**Fix:** Clear the memory only when a fingerprinted path, or a path relevant to the lead, changed:
```python
relevant = [p for p in touched
            if p == rep.get("file") or p in fingerprint
            or _is_associated_test(p, rep.get("file"))]
... or relevant):
    del rep["recheck_settled"]
```
Mirror the same filter in the `20-dispatch.md` skip rule. Add a test that an unrelated touched path does not clear the memory.

## Warnings

### WR-01: `fix` and `codex-adversarial` can still confirm through an unbound plain request

**File:** `plugins/vibe-check/scripts/score.py:1320-1328`
**Issue:** `_routed_request_ok` rejects never-confirmers only when a plain request carries `snapshot_blob`. A plain request without that key passes with `agents: ["fix"]` or `["codex-adversarial"]`, and that agent's `resolved` closes a `needs-recheck` record. Reproduced: `resolution.agents == ["fix"]` and `["codex-adversarial"]`, with no rejection. The prose now says every plain entry carries `snapshot_blob`, so the unbound shape is only an escape hatch. But the scorer is documented as the authority ("a verdict can only act through score.py's token/agent guard"), and the stated safeguard is "never".
**Fix:** Apply `not any(a in _NEVER_CONFIRMERS for a in req["agents"])` to every request shape at the top of `_routed_request_ok`, before branching on `route`.

### WR-02: The confirmed-fix route accepts `codex-adversarial` as the confirmer, against the prose

**File:** `plugins/vibe-check/scripts/score.py:1329-1334` (`_FIXER_AGENTS` only); `plugins/vibe-check/phases/review/20-dispatch.md:101,106`
**Issue:** `20-dispatch.md` step 3 says "`codex-adversarial` and `fix` are never the reviewer". Step 4 says score.py accepts a routed verdict "never from `fix` or `codex-adversarial`". But the `confirmed-fix` branch checks only `_FIXER_AGENTS = {"fix"}`. `_routed_request_ok({... "route": "confirmed-fix", "agents": ["codex-adversarial"] ...})` returns `True`. This is prose-vs-scorer contract drift on a stated safeguard.
**Fix:** Use `_NEVER_CONFIRMERS` in the confirmed-fix branch. Add a request-shape subtest next to `test_never_confirmers_rejected`.

### WR-03: A still-applies on one route does not block a resolution on another; the persisted case emits both a rejection and a closure

**File:** `plugins/vibe-check/scripts/score.py:1494-1538` (`_accept_verdict`), `1382` (`_independent_recheck` checks only `independent`)
**Issue:** `_independent_recheck`'s docstring promises "nobody asked says it still applies", but it looks only at independent-token verdicts. Reproduced on one lead with a bound plain request (raising lane answers `still-applies`) and an independent request (`bugs` answers `resolved`):
- `needs-recheck`: the lead closes with no rejection.
- `persisted`: `filtered[]` gets `fix not confirmed: the routed reviewer says it still applies`, the lead is also in `resolved[]`, and `_judge` writes `recheck_settled` onto the resolved record.

The prose currently keeps the two routes disjoint (the lane is dispatched or it is not), so this needs an orchestrator slip to trigger. But contradiction handling is the scorer's job.
**Fix:** In `_accept_verdict`, compute `still = any(v["verdict"] == "still-applies" for v in matched + independent + routed)` and refuse any resolution when it is true, rejecting with `verdict: contradicted by still-applies`.

### WR-04: New crash on a carried record with an unhashable `file` (regression against HARDEN-01)

**File:** `plugins/vibe-check/scripts/score.py:2005-2006` (also `1387`, `1403`, `1534`)
**Issue:** `head_blobs.get(record.get("file"))` raises `TypeError: unhashable type: 'list'` when a carried record's `file` is a list or dict and any pending verdict matches it. `_valid_finding` documents that a non-str `file` must flow through, not crash. Reproduced: the previous `score.py` (8df9545) scores the same envelope and resolves the record; the new one crashes, even with no `head_blobs` in the envelope.
**Fix:** Guard the lookups: `blob = head_blobs.get(file) if isinstance(file, str) else None`. A helper `_head_blob(file)` used at all four sites keeps them consistent.

### WR-05: `applied` fix verdicts are never pruned, so every later pass reports a stray `verdict: record not carried`

**File:** `plugins/vibe-check/phases/review/05-state.md` (`$FIX_VERDICTS_PREV`), `plugins/vibe-check/scripts/carry_state.py` (no removal path), `plugins/vibe-check/scripts/score.py:2211-2214`
**Issue:** `05-state.md` now forwards every `applied` entry at any age and says it "leaves `fix_verdicts` only when its item closes through `resolved[]` or the owner decides it". No code removes it. `record_fix_verdicts` is the only writer and it only adds. Once the item closes, the entry is still forwarded every pass and no carried record consumes it. Verified: `score.run` with such an orphan returns `{'file': None, 'line': None, 'title': None, 'reason': 'verdict: record not carried'}` in `filtered[]`, and this happens on every pass, permanently.
**Fix:** Do one of the following:
- Have `carry_state.py` drop an `applied` entry whose hash appears in any `passes[].resolved[]` or has a current decision (at persist or finalize).
- In `05-state.md`, forward an `applied` entry only when its hash is in `state.passes[-1].findings`.

Either way, make the prose claim true.

### WR-06: `_is_associated_test` matches on the basename stem alone, across directories

**File:** `plugins/vibe-check/scripts/score.py:1259-1276`
**Issue:** Association compares only `bare == _path_stem(src_file)`. Any changed `**/index.test.ts`, `**/utils.spec.ts` or `**/test_config.py` therefore counts as "an associated test" of every `index.ts` / `utils.ts` / `config.py` in the repo. That satisfies `_independent_trigger` for a `persisted` record whose own code and real tests never changed. This trigger is the only guard that a pinned-unchanged record had something relevant change.
**Fix:** Require directory affinity too. For example, the test's directory minus its test segments (`test`, `tests`, `__tests__`, `spec`) must be a suffix or prefix of the source's directory. Or require that the mirrored path after stripping a leading `src/` or `tests/` root matches. Add negative cases (`src/a/index.ts` vs `tests/b/index.test.ts`) to `test_associated_pairs`.

## Info

### IN-01: The iPlayarr fixture is not "trimmed to minimal fields"

**File:** `plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json`
**Issue:** The file is 90 KB with 18 findings across 3 passes. It carries full `problem` prose, `why_it_matters`, `fix_hint`, `current_code`, `source_window` code excerpts, an `intent_doc_match` quote from `45-08-PLAN.md`, real commit SHAs in `head_sha`/`diff_range`, and run timestamps. Commit 7b7f0d3 calls it trimmed. Nothing sensitive was found: no credentials, emails, hostnames, absolute home paths or tokens, and `thejuran/iplayarr` is public.
**Fix:** Optional. Strip fields the tests don't read (`problem`, `why_it_matters`, `fix_hint`, `intent_doc_match`, `timestamp`) so the fixture matches its description and stays small.

### IN-02: Formatting slip

**File:** `plugins/vibe-check/scripts/score.py:1894`
**Issue:** `threshold =THRESHOLDS.get(...)`: the space after `=` was lost in the edit.
**Fix:** `threshold = THRESHOLDS.get(command, THRESHOLDS["review"])`.

### IN-03: Render prose is ambiguous for a Needs-verification row that receives a `verdict: fix not …` reason

**File:** `plugins/vibe-check/phases/review/40-render.md:41-43`
**Issue:** A Codex-raised Needs-verification lead with no confirmed fix gets the independent route and therefore `verdict: fix not …` reasons. The NV-row rule looks only for `verdict: confirmed fix`. The next rule applies to "every OTHER open row (any section)", and it is unclear whether NV rows count as "other". A model rendering this may drop the reason from the NV row.
**Fix:** State explicitly that NV rows also take the `verdict: fix not` line when no `verdict: confirmed fix` reason exists.

## Set aside (needs ruling)

### SA-01: The independent route can close a Needs-verification item without an owner decision or a named fix

**Where:** `plugins/vibe-check/scripts/score.py:1358-1388` (no band check); `plugins/vibe-check/phases/review/20-dispatch.md:96`
**Why excluded:** This looks like a design choice, not a bug. The removed prose said a Needs-verification item from a non-dispatched lane "closes by an owner decision, or after an owner-named fix". Now any eligible ladder confirmer's `resolved` (with a blob match) closes it as source `recheck`.
**Effect if left as is:** Codex-raised Needs-verification items can leave the report on one native reviewer's word, with no owner card and no fix commit.
**Needs:** A ruling that this is in scope for Phase 56, or a band guard to restore the previous behavior.

### SA-02: Plain re-checks of `needs-recheck` records still ignore `snapshot_blob`

**Where:** `plugins/vibe-check/scripts/score.py:1497-1520`
**Why excluded:** This is pre-existing behavior. The bound rule is applied only to `persisted` records by design, and the gitsnap compare guards the window between dispatch and collect.
**Effect if left as is:** A `needs-recheck` record can close on a plain `resolved` while the file is dirty or differs from what the reviewer read. The prose now says every plain entry carries `snapshot_blob`, which suggests the binding applies.
**Needs:** A decision to defer or to accept.

---

_Reviewed: 2026-10-23_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
