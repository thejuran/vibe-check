# Fable — cold adversarial review of vibe-check `score.py` (tag v2.7)

**Reviewer:** Fable 5 (independent second-model pass)
**Scope of this file:** the Python scoring engine only — `plugins/vibe-check/scripts/score.py` and its contract in `commands/review.md` Phase 3. The security-critical bash pass (path containment, Codex normalization, chunk math) is NOT in this file; run it separately.
**Checkout:** `HEAD 3501545` (tag `v2.7`).
**Method:** every finding was confirmed by running the actual `score.py` at v2.7 against crafted input in a scratchpad — no repo edits. Where a finding is disputable, the repro is the adjudication.

## Transparency note
Project memory indicates a later milestone (Phase 32, *after* v2.7) caught "a review-HALTING crash (unhashable file)" in its own dogfood. Finding **3** below overlaps that class. It was found here independently by reading v2.7, it is live and untested at v2.7, and this version covers two field types + a distinct surrogate trigger — but the overlap is flagged so it can be weighed honestly.

---

## Independent verification (Opus, 2026-07-01)

Each finding was checked against the real `score.py` extracted at tag `v2.7`
(`git show v2.7:…/score.py`), reading the cited lines and surrounding logic. This is a
**read/structural** verification (mechanism confirmed present as described), not a re-run of the
crafted-input repros. **This review WAS genuine Fable** (it completed before the safeguard
model-switch that hit the later bash pass — see `fable-findings-bash-v2.7.md`), so it stands as a
real independent second-model data point. One finding did not survive.

**8 of 9 confirmed real; F5 overstated (the code already guards the scenario).**

| # | Finding | Verdict | Verifying evidence |
|---|---------|---------|--------------------|
| 1 | tie-break representative order-dependent | ✅ CONFIRMED (HIGH) | `score.py:805-808` — stable sort + `[0]`; representative supplies `stable_hash` |
| 2 | agent-forged `status:"persisted"` grants +15 | ✅ CONFIRMED (HIGH, security) | `:955`; `_valid_finding` (853) is crash-safety-only, never scrubs `status` |
| 3 | malformed finding crashes the whole run | ✅ CONFIRMED (HIGH) | `_valid_finding` dict-check-only; `SEVERITY_WEIGHT.get(severity)` :292 + `stable_hash.encode()` :59 crash on non-hashable / surrogate |
| 4 | NaN → invalid JSON on passthrough | ✅ CONFIRMED (MED–HIGH) | `json.dump(...sys.stdout)` :983, no `allow_nan=False`; the :264-274 guard only coerces `agent_confidence` for score math, not output |
| 5 | window-widen misalignment | ❌ **OVERSTATED — not a real bug** | `_carry_key` is symmetric (first ≤3 non-blank lines each side); widen needs BOTH sides ≥2 non-blank (:211-213); **review.md:686 documents that a single-line `}` vs unchanged HEAD stays `persisted`** — the exact example is the documented counter-case |
| 6 | out-of-diff findings emitted despite docstring | ✅ CONFIRMED (MED) | `_score_member` returns `drop:True` only when `score is None` (:965); `in_diff` never drives a drop, only the +20 bonus |
| 7 | silenced-marker misses `//nolint`/`#noqa` variants | ✅ CONFIRMED (MED) | `SILENCED_MARKERS` :40 has `"// nolint"`/`"# noqa"` **with space**; substring match, no `.lower()` — Go's `//nolint` + `#noqa`/`# NOQA` escape the −50 |
| 8 | intent-doc drop mislabeled `sub-threshold` | ✅ CONFIRMED (LOW) | `reason = "silenced" if silenced else "sub-threshold"` :966 |
| 9 | `_line_in_ranges` guards length not element type | ✅ CONFIRMED (LOW–MED) | :908 `pair[0] <= line <= pair[1]` on `["8","14"]` → `TypeError` str vs int |

**Takeaway:** an excellent hit rate for a cold second-model pass. The single miss (F5) is a
plausible claim where the code has an *explicit documented guard* (review.md:686) Fable didn't
see — exactly the failure mode adversarial review is prone to; verifying caught it. The bash pass
is in the companion file `fable-findings-bash-v2.7.md` (Opus-authored, 5/5 confirmed).

---

## Ranked findings (verdict-changers first)

### 1 — Tie-break representative is input-order-dependent → dismissal keys unstable across passes  [HIGH]
**`score.py:804-806` (+ member ordering `:560-567`).**

`scored_members.sort(key=lambda t: t[0], reverse=True)` is stable, so among equal-top-score members of a cross-confirm group the *representative* is just the first in `g["members"]`, whose order is the input (agent-return) order. That representative supplies the emitted `title`/`file`/`line` **and the `stable_hash`** — which is the dismissal key for `medium_acknowledgments[stable_hash]`.

**Trigger → wrong output:** two co-located same-domain findings that tie after scoring — e.g. `injection`@10 (security) and `auth`@11 (bugs), both reaching 95 with the +10 cross-confirm. Input `[A,B]` emits representative **A**, `stable_hash aac1524e…`; input `[B,A]` emits **B**, `stable_hash 58ec18ea…`. Same two findings, different order → different persisted dismissal key. A Medium the owner dismissed on one pass silently re-surfaces as unacknowledged on the next when agent-return order differs (nondeterministic across runs).

**Tests:** grouping/attribution order-independence is covered (`test_*_every_ordering`); the representative's identity across permutations is **not**. Uncovered.
**Why it matters:** silently defeats the acknowledge-a-Medium workflow and changes which finding the report leads with — the PM cannot catch this.

### 2 — Agent-controlled `status:"persisted"` grants +15 (unverified scoring input)  [HIGH]
**`score.py:955`** — `persisted = id(member) in persisted_ids or member.get("status") == "persisted"`.

Hard-rule #4 makes the orchestrator recompute `in_diff` and `silenced` from raw facts, overriding agent self-reports. But `status` is *also* a scoring input (+15) and is **not** scrubbed. `review.md:726` passes agent findings through "enriched with `agent`, `source_window`, `canonical_line_content`" — it never strips other keys. So a finding arriving with `"status":"persisted"` (an agent emitting an extra field; the reviewed diff may be attacker-authored per the tool's own fix-agent warning) takes the +15.

**Confirmed consequences:**
- Band flip: conf 65 in-diff = 85 (**warning**) → forged = 100 (**critical**), rendered `status: persisted`.
- Threshold resurrection under `/review`: conf 45 in-diff = 65 (filtered `sub-threshold`) → forged = 80 (**reported**).

**Tests:** none feed a pre-scored `status` on a non-carryforward finding.
**Why it matters:** an untrusted input crosses a band boundary, resurrects filtered findings, and falsely labels a fresh finding "PERSISTED (pass N)".

### 3 — One malformed finding hard-crashes the entire review  [HIGH]
**`score.py:292, :953, :945-946, :81-83`** — three live crash surfaces `_valid_finding` (`:874`, dict-check only) lets through:
- `severity` non-hashable (`["high"]`, `{…}`) → `SEVERITY_WEIGHT.get(severity, …)` **TypeError** (`:292`).
- `file` non-hashable → `changed_line_ranges.get(file, [])` (`:953`, diff mode) / `file in reviewed_union` (`:945`, --all) **TypeError**.
- `title`/`file`/`canonical_line_content` with a lone surrogate (`"\ud800"`, legal JSON, accepted by `json.load`) → `stable_hash`'s `.encode()` **UnicodeEncodeError** (`:82`).

Each raises out of `run()`; the `__main__` shim deliberately doesn't catch it; the process exits non-zero; the orchestrator's fail-closed gate (`review.md` Phase 3 step 5) **HALTS the whole review** — the good sibling in the same envelope is lost too (confirmed).

**Tests:** the T1–T21 malformed matrix exists to prevent exactly this, and covers odd `line`, odd `source_window`, non-finite confidence, non-dict containers, null fields — but **not** non-hashable `file`/`severity` and **not** surrogate text. The hardening effort's own stated guarantee is violated by field types that slipped the net.
**Why it matters:** availability defect — a single bad agent finding (or attacker-influenced content) takes down the whole review. Overlaps the Phase-32 "unhashable file" dogfood find (see transparency note); two field types + surrogates remain open at v2.7.

### 4 — `score.py` emits invalid JSON on any non-finite passthrough value  [MEDIUM-HIGH]
**`score.py:983` (`json.dump` default `allow_nan=True`), survivor copy at `:808`.**

The non-finite guard (`:271-275`) only coerces `agent_confidence` for the score math — it does not sanitize the value written to stdout. `survivor = dict(best_member)` copies the raw finding, so a `NaN`/`Infinity` anywhere the agent controls (`intent_doc_match.confidence`, or even the "guarded" `agent_confidence`) reaches `json.dump` and is written as the bare token `NaN` — **not valid JSON**. Confirmed: a surviving finding with `intent_doc_match:{confidence:NaN}` produces stdout a strict parser (`jq`, any non-Python consumer) rejects.

**Tests:** T21 checks the score is 0 and no crash; it does **not** assert the output is valid JSON.
**Why it matters:** depending on how the orchestrator parses, this either trips the fail-closed "not valid JSON → review halted" branch (whole review lost) or silently corrupts a strict-JSON downstream. The guard added specifically for non-finite values is incomplete.

### 5 — `canonical_window` widen compares misaligned windows → unchanged low-entropy findings falsely flip to `needs-recheck`, losing +15  [MEDIUM]
**`score.py:210-218` + `_carry_key` `:146`, against the window `review.md:686` actually builds.**

`review.md:686` builds `canonical_window` = the HEAD line **plus its next ≤2 non-blank lines**. For a stored 2-line snippet (`}` + `doThingA()`) whose HEAD is unchanged, the HEAD window is 3 lines. The widen branch then compares `_carry_key(current_code)` (first ≤3 non-blank = **2** lines) against `_carry_key(canonical_window)` (**3** lines) — different by construction → `needs-recheck`. Confirmed: an unchanged `}\n  doThingA()` returns `needs-recheck`.

This regresses the exact feature (ROBUST-03) added to stop false flips for low-entropy first lines. It costs the finding its +15 persisted bonus and triggers an unnecessary agent re-dispatch every pass.
**Tests:** `TestCarryForwardLowEntropyWindow` only passes **equal-length** windows (both sides identical line sets); it never exercises the real asymmetry `review.md` produces. The suite validates a window shape the orchestrator doesn't build. Uncovered.

### 6 — `_score_member` docstring says out-of-diff findings are dropped; the code emits them  [MEDIUM]
**`score.py:919` vs `:952-953`.** Docstring: "diff mode: out-of-diff findings are dropped (reason 'out-of-diff')." Reality: `in_diff` is computed only as the +20 bonus flag; there is **no drop**. A confident out-of-diff finding (conf 95, line outside the changed range) is emitted at score 95 / band critical under `/review`. Contradicts both the docstring and `review.md:975` "Never report pre-existing (orchestrator verifies in_diff)."

**Tests:** `test_in_diff_recomputed_overrides_agent_claim` actually **asserts** the keep-at-85 behavior — so the code is "tested," but the test locks behavior the docstring and the user-facing promise both deny. The defect is the three-way contradiction: the PM is promised pre-existing code won't be flagged, and high-confidence pre-existing findings are.
**Note:** partly self-limiting (missing +20 pushes many out-of-diff findings below threshold), but the guarantee is false and the docstring is objectively wrong.

### 7 — Silenced-marker match misses real-world suppression directives (notably Go `//nolint`)  [MEDIUM]
**`score.py:40-41, :105-108`.** `SILENCED_MARKERS` are fixed substrings with a space: `"// nolint"`. Go's actual machine directive is `//nolint` (**no space** — golangci-lint requires it). Confirmed: `silenced_nearby(["x //nolint:errcheck"])` → **False**. So a finding the author legitimately suppressed with a valid Go directive gets **no −50** and is **reported**. Same for `#noqa` (no space) and `# NOQA` (uppercase), both valid flake8. The scanner is also case-sensitive.

**Tests:** `TestSilencedNearby` only tests the exact canonical spellings.
**Why it matters:** the tool surfaces findings the author explicitly silenced — noise against its own "respect suppression" contract, hitting every Go user.

### 8 — Filtered-reason mislabels an intent-doc drop as `sub-threshold`  [LOW]
**`score.py:964-968`.** When `_intent_doc_penalty` (−100 strong match) drives pre-clamp < 0, the drop reason is `"silenced" if silenced else "sub-threshold"`. So a finding dropped because the code matches the plan (intent-doc strong match) is reported as `sub-threshold`. `scoring.md:64` makes filtered reasons user-facing. The label is also reused by the genuine threshold filter (`:829`), so two distinct drop mechanisms are indistinguishable in the report.
**Why it matters:** reporting-accuracy, not a wrong verdict — but it misinforms the owner about *why* something was filtered.

### 9 — `_line_in_ranges` guards pair length but not element type  [LOW-MEDIUM]
**`score.py:908`.** `if len(pair) >= 2 and pair[0] <= line <= pair[1]` — a range pair with string elements (`[["8","14"]]`) raises `TypeError: '<=' not supported between 'str' and 'int'`. `changed_line_ranges` is orchestrator-built (LLM-assembled JSON from git hunks), and string line numbers are a plausible drift. Same element-vs-container hole they fixed for `source_window` (`_safe_window` HOLE 1) but left here.
**Why it matters:** robustness gap → potential review halt from an orchestrator-side type drift; narrower reach than #3 since the input isn't agent-controlled.

---

## Brief items checked and dropped
- **`config.py` / `_MEDIUM_FLOOR` drift, `min_confidence` label (brief #2, #4):** `config.py` does **not exist at tag v2.7** (only `score.py` + `test_score.py` in `scripts/`). Landed in a later milestone; not reviewable here.
- **`persisted` via `id(member)` reaching a both-miss path (brief #3):** the `id()` path is sound for carryforward (no intervening dict-copy between `persisted_ids.add(id(cf))` and the same-object read). The real defect on that line is the unverified `status` fallback — finding **2**.
- **`_line_in_ranges` inclusive endpoints / band boundaries (brief #6):** band boundaries are exhaustively tested; the inclusive `pair[0] <= line <= pair[1]` is correct. No off-by-one.

## Summary
The scoring math (weights, clamp, drop rule, mutual-exclusion, band cutoffs) is solid and well-pinned. The defects cluster at **trust boundaries and malformed-input edges** the golden-digest/formula tests don't reach: an unverified scoring input (#2), a representative-selection nondeterminism the order-independence tests skip (#1), and a malformed-input hardening effort with three specific gaps still open (#3, #4, #9). Findings **1, 2, and 3** can silently hand the PM a wrong verdict or a dead review, so they rank first.

## Repro artifacts
Runnable repros used to confirm every finding above (not committed; scratchpad only):
- `repro.py` — findings 1, 2, 3, 4-passthrough, 5, 6, 7, 9
- `confirm2.py` — band-flip / threshold-resurrection (2), NaN strict-parse failure (4), `_valid_finding` passthrough + whole-review halt (3)
