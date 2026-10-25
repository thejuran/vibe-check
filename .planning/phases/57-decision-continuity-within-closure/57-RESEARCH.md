# Phase 57: Decision continuity within closure - Research

**Researched:** 2026-10-25
**Domain:** vibe-check carry-forward state: finding identity (`stable_hash`), owner decision evidence binding (`carry_state.py`), site grouping / members (`score.py`), finalize card (`batch_card.py`, `90-finalize.md`), orchestrator HEAD reads (`30-collect-score.md`)
**Confidence:** HIGH for the reproduction verdicts (every one was produced by running the real `score.run` → `append_pass` → `carry_state` / `batch_card` chain on current code at 9be39a8). MEDIUM for the recommended mechanisms (designed from the code, not yet built).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Current behavior (scouted 2026-10-25 — the baseline these decisions change)
- Decisions live in the root `decisions` family keyed by `stable_hash` (file + canonical line content + title), written only by `carry_state.py record-decisions`. Kinds: `dismiss`, `defer` (`carry_state.py:111`).
- Evidence binding (`carry_state.decision_state`, `carry_state.py:457`): an ordinary finding's decision stays current only while `file`, `line`, `canonical_line_content`, `band` all equal the decision-time evidence. So a **pure line shift** (code added above) and **any band move (up or down)** make it stale → re-asked. An edit to the flagged line re-hashes it (new hash, no decision); the finalize helper links an edited finding to the earlier decision when exactly one row matches (`90-finalize.md:106`).
- Needs-verification decisions use `_NV_EVIDENCE_KEYS` = file, canonical_line_content, band, `current_code` fingerprint (no line): a line shift keeps the decision, a body change re-asks (`carry_state.py:393`).
- Rows: a decision on a LEAD row closes nothing for its `members[].obligation` records — each member is its own finding deduped by its own `stable_hash` (`90-finalize.md:25`, `carry_state.py:25-29`).
- Reopen card already shows the earlier decision and reason: "code changed since your decision on pass N (was: dismissed — reason)" / "severity changed (A → B) since your decision on pass N" (`90-finalize.md:101-104`).
- Phase 56 added the D-04 "nearby change" window (5 lines beneath the pinned line) and file/associated-test touch triggers in `score.py` for re-checks.

#### What reopens a decision (target behavior; change only where a failure reproduces)
- **D-01:** A pure line shift (code added/removed above; the flagged line itself unchanged) does NOT reopen a decided finding — the decision follows the code. (Today it re-asks → reproduce as a lost decision.)
- **D-02:** A change to code immediately around the flagged line (same nearby window as Phase 56's D-04 trigger) DOES reopen it — relevant evidence changed (DECN-03).
- **D-03:** An edit elsewhere in the same file, outside that nearby window (e.g. a different function), does NOT reopen it (DECN-02).
- **D-04:** Needs-verification decisions keep today's rule: any change to the recorded code body re-asks; a line shift does not.

#### Severity changes
- **D-05:** A band RISE on unchanged code (e.g. corroboration by another reviewer) reopens the decision — stronger evidence counts as new evidence; the card says it rose and why.
- **D-06:** A band DROP on unchanged code does NOT reopen it — weaker evidence never needs the owner again. (Today any band move re-asks → reproduce.)
- **D-07:** Defer and dismiss follow the same severity rule.

#### Regrouping rows
- **D-08:** When a decided finding is merged into a row with other findings, the decision still covers that finding (it shows as already decided); the owner is asked only about findings the decision did not cover. A decision never silently covers a different reviewer's new concern at the same spot.
- **D-09:** When a decided row is split into separate rows, every finding the decision covered stays decided; only genuinely new findings are asked.
- **D-10:** A row mixing a decided finding with new ones shows a short note, e.g. "1 finding here already dismissed (your reason: …)".

#### Defer vs dismiss on reopen
- **D-11:** A deferred finding does NOT resurface on its own (no timer/expiry) — defer and dismiss both stay put until relevant evidence changes.
- **D-12:** When a decided finding reopens because evidence changed, the card shows the earlier decision, its reason, and what changed (line-near-edit / severity rise / code body) — extend the existing stale suffix rather than presenting it as brand new.
- **D-13:** A deferred finding that later gets fixed closes normally through the Phase 56 path ("Closed — fix confirmed …"); the deferral does not block closure.

#### Carried forward (locked from earlier phases)
- Reproduce first; non-reproducing paths are recorded and dropped, never replaced with invented work (owner rule, v2.13).
- Never re-ask without new evidence (v2.11 rule; Phase 56 D-09).
- Single-writer rule: only `carry_state.py record-decisions` writes `decisions`; old records are never rewritten (superseded ones go to `history`). Legacy decisions without `evidence` keep closing as before.
- Mutation-test every new guard; existing suite and replay gate stay green; GOLDEN_DIGEST / `stable_hash` frozen (changing the hash would orphan every persisted dismissal).

### Claude's Discretion
- How a decision "follows" a shifted line (relocation by canonical content, a line-free evidence key set for ordinary findings, or similar) — as long as `stable_hash` stays frozen and legacy records still read correctly.
- How "band rise vs drop" is detected and stored (ordering of bands, evidence comparison) and the exact card wording for D-05/D-10/D-12.
- How member-level decision coverage is tracked across merges/splits (per-member decision records vs lead coverage list), within the single-writer rule.
- Whether D-02's window is literally Phase 56's 5-line-beneath window or a symmetric window, as long as it is shared with the re-check trigger and documented.

### Deferred Ideas (OUT OF SCOPE)
- Timed reminders / expiry for deferred findings (resurface after N runs or at milestone close-out) — owner declined for this phase; would be a new capability.
- Broader duplicate presentation and cross-repo gate consumers — excluded by ROADMAP.
- Recovery wording across all cards — Phase 58 (RECV-02).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DECN-01 | A lost defer/dismiss decision on regrouping or unrelated edits is reproduced before any identity rule changes; if it does not reproduce, that is recorded and the work dropped | §Reproduction Verdicts: 7 paths reproduce (R1–R7), 6 do not (N1–N6), each with the probe that showed it. Wave 0 turns R1–R7 into committed failing fixtures and N1–N6 into "did not reproduce; dropped" notes |
| DECN-02 | Owner defer/dismiss decisions survive regrouping and edits unrelated to the finding's evidence | R1 (line shift), R3 (band drop / persistence noise), R5 (Phase-46 dedup drops the decided obligation), R6 (split re-asks a covered member) → Patterns 1, 3, 4, 5 |
| DECN-03 | A decided finding reopens when its relevant evidence changes | R2 (edit next to the flagged line keeps the decision), R4 (new concern silently covered by a decided row) → Patterns 2, 4; card wording Pattern 6 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

There is no `./CLAUDE.md` in the repo and no `.claude/skills/` or `.agents/skills/`. The binding directives come from the owner's global instructions and project memory:

- **Owner is a PM, not a developer.** Technical choices belong to Claude. Bring the owner product questions only, framed by user impact, risk, time and maintenance. "Looks good" on a diff means "proceed", not "reviewed". Proof comes from tests.
- **Scope discipline (2026-10-17):** new work only for four classes: a REPRODUCED gate failure, data loss, silent finding loss, or a broken required workflow. Everything else is carried. Reviews look only at changes.
- **No paid runs** (API/model measurement) without a separately approved, bounded proposal. Every reproduction in this research is local: pure Python, no model calls.
- **Mutation-test every guard** (memory: "Decorative guards", 6 of 8 Phase-40 plans shipped guards that could never trip). Assert that fixtures contain what you think they contain.
- **Rewrite breadth is the risk** (Phase 40 adversarial arc). Keep each fix scoped to its reproduced path.
- **One branch/PR per phase:** `feat/v2.13-phase-57` (current). `.planning/` is gitignored, so tracked planning files need `git add -f`.
- **Shell:** the Bash tool runs zsh. Run multi-line shell as `bash -s <<'BASH' … BASH`. Bare `pytest` works; `python3 -m pytest` does not.
- **Security (absolute):** never log tokens/PII. Finding text is attacker-influenced: card text is DATA, flattened, never executed. Reasons never carry a hash, title or path (`carry_state` REASONS convention).
- **Planning format:** follow `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md` for STATE/ROADMAP edits.

## Summary

I reproduced every CONTEXT scenario on current main (9be39a8) using a throwaway local probe (`$SCRATCHPAD/probe57.py`). It drives the real scorer and helpers across two passes and simulates the orchestrator's HEAD reads exactly as `30-collect-score.md` step 0 specifies. **Seven paths reproduce and six do not.** The probe also surfaced one confound that changes how D-05 should be planned.

What reproduces:

1. **Pure line shift (D-01).** The decision is lost in two ways. Ordinary carried findings are read at their stored line, not relocated (`30-collect-score.md:53`: "general relocation is out of scope"). After code is inserted above, the carried row points at the wrong code. If the row stays above threshold, it is re-hashed to a new `stable_hash`, the decision is orphaned, and the row is re-asked as "code changed". If it falls below threshold, it is kept open as stale, cause "code". When the reviewer re-reports the finding at its new line, the owner gets two rows for one finding.
2. **Edit within the 5 lines beneath the flagged line (D-02).** The decision stays current, so the finding is wrongly kept.
3. **Band moves on unchanged code.** These are endemic. The +15 persistence bonus, and the lone-lane cap that persistence releases, push most findings decided on pass 1 up one band on pass 2 with **no code change at all**. A "severity changed" re-ask then follows. Drops also re-ask (D-06 reproduces).
4. **A different reviewer's new, weaker concern** absorbed into a decided row is never asked. That is silent finding loss.
5. **The Phase-46 accepted residual still exists.** A fresh duplicate of a decided finding can out-rank it in a group led by a third finding. The decided record's obligation identity is then dropped and its decision orphaned.
6. **A member covered by a decided row** comes back as a brand-new undecided row when the row splits, for example when the lead is resolved.
7. A rise gets no "why" on the card (this is how D-05/D-12 read today).

What does NOT reproduce:

- A same-file edit outside the window with no line shift (D-03): the code evidence holds. It is only re-asked because of the band noise in item 3.
- A stronger new finding leading a row that holds a decided finding: the decision is kept. Only the D-10 note is missing.
- An edit to the flagged line itself: it is linked correctly.
- NV line shift (D-04).
- No-expiry (D-11).
- Defer then fix closing normally (D-13).
- The real iPlayarr data has no lost-decision instance. Its only two real defers (pass 1, `format-53/…archived-2026-10-20-2`) closed through recheck on pass 2.

**Primary recommendation:** Fix only R1–R7, using the machinery that already exists:

- **(a) Line shift.** Extend Phase 53's relocate-by-content rule (`30-collect-score.md` cases 1–3) to ordinary carried records that hold a current decision. Compare ordinary decision evidence without `line`, as NV already does.
- **(b) Edits next to the line.** Add one shared `_nearby_changed` helper, split out of Phase 56's `_independent_trigger`. It stamps a `nearby_at` key on the snapshot that decision evidence compares.
- **(c) Severity.** Make the comparison direction-aware: a drop keeps the decision, a rise reopens. Which rises count needs an owner ruling (Open Question 1).
- **(d) Regrouping.** Record the row's covered member identities on the decision record (`covers`, written by the single writer `record-decisions`). A carried row's newcomers are then asked, and covered members that split off keep the decision.
- **(e) Phase-46 dedup.** Fix the member dedup so a carried obligation is never dropped when a fresh duplicate out-ranks it.

`stable_hash` and GOLDEN_DIGEST do not move.

## Reproduction Verdicts (DECN-01 — the phase gate)

Probe: `/private/tmp/claude-501/-Users-julianamacbook-turingmind-code-review/ece7577f-1045-4138-8d0b-6a248a0e3637/scratchpad/probe57.py`. It is throwaway, not committed, and imports `score`, `carry_state`, `batch_card` and `test_carry_state.append_pass`. Every row below comes from running it [VERIFIED: local probe on 9be39a8]. "Band-stable" means the inputs were chosen (conf 70, pass-2 diff not touching the flagged line) so that the band noise in R3 does not hide the code-path result.

| # | Scenario | Today (probe output) | Target | Verdict | Class (scope rule) |
|---|----------|----------------------|--------|---------|--------------------|
| R1a | +3 lines above, no re-report, row above threshold | carried row stays at line 10 (now other code) → `needs-recheck` → **re-hashed** `dee0f534→ec3d5f64`; decision orphaned; card: "code changed since your decision" (successor link) | KEPT (D-01) | **REPRODUCES** | lost decision; re-ask w/o new evidence |
| R1b | same, band-stable (row sub-threshold) | kept-open row keeps `dee0f534`, snapshot canonical = wrong line → stale `code` → re-asked | KEPT | **REPRODUCES** | same |
| R1c | +3 lines above AND reviewer re-reports at line 13 | TWO rows: phantom carried row `ec3d5f64` at line 10 (undecided, asked as new) + fresh `dee0f534` at 13 (stale `code`, line differs) | KEPT, one row | **REPRODUCES** | same + duplicate row |
| R2 | flagged line unchanged; line 11 / 13 / 15 (1, 3, 5 beneath) edited; band-stable | decision `current`, card empty | REOPEN (D-02) | **REPRODUCES** (wrongly kept) | DECN-03 |
| R3a | unchanged code, pass 1 → pass 2, lone lane | band moves warning→critical for conf ≥ 80 (pass-2 line not in diff) and conf ≥ 65 (in diff); medium→warning too; card "severity changed (warning → critical)" | — see Open Question 1 | **REPRODUCES** (re-ask w/o new evidence) | broken required workflow |
| R3b | band drop on unchanged code (warning→medium; also observed naturally at conf 65–70 when pass-2 line leaves the diff) | stale `severity` → re-asked | KEPT (D-06) | **REPRODUCES** | lost decision |
| R4 | decided A; new weaker `security` finding B at line 11 absorbed into A's row | B is a member with **no obligation** → not an open record → counts 0/0/0, gate writes; B never asked | B asked (D-08) | **REPRODUCES** | silent finding loss |
| R5 | decided A (conf 60); fresh duplicate of A (conf 100) + third finding C whose hash sorts first | C leads; fresh A-dup wins member dedup (`_finding_identity`), carried A's obligation is never attached → `dee0f534` no longer an open record; decision orphaned; no successor link (titles differ) | A stays decided (D-08) | **REPRODUCES** (= Phase-46 accepted residual 1, `46-CONTEXT.md:136`) | lost decision; obligation loss |
| R6 | pass 1 row: lead B (security, 12) + member A (bugs, 10); owner dismisses the row; pass 2 B resolved by recheck | A becomes its own row `dee0f534`, undecided, no link to the earlier decision, asked as brand new | A stays decided (D-09) | **REPRODUCES** | lost decision |
| R7 | band rise on unchanged code (forced) | reopens with "severity changed (medium → warning)": no "why" | reopen + why (D-05, D-12) | partial: reopen already happens; wording gap | card wording only |
| N1 | same-file edit at line 40, no shift; band-stable (with and without re-report) | decision `current` | KEPT (D-03) | **did not reproduce; dropped** (band noise R3 is the only cause of re-ask) | — |
| N2 | stronger new finding B leads; decided A becomes a member | A keeps obligation `dee0f534`, decision `current`; only B asked | KEPT (D-08) | **did not reproduce** (decision kept); only the D-10 note is missing | presentation |
| N3 | flagged line itself edited + re-report | new hash, successor link "code changed (was: dismissed — …)" | REOPEN, linked | **did not reproduce** (works) | — |
| N4 | NV line shift / body change (D-04) | relocation by content + `_NV_EVIDENCE_KEYS` already (Phase 53) | keep | **did not reproduce** (existing tests `TestDecisionEvidence` NV cases) | — |
| N5 | deferred finding, no change, many passes (D-11) | no timer; `TestNoExpiry` pins no age input | keep | **did not reproduce** | — |
| N6 | deferred finding, flagged line fixed + recheck `resolved` (D-13) | `resolved[]` = `dee0f534`, counts 0, findings [] | closes | **did not reproduce** (works) | — |
| — | title drift: same agent re-reports A with a new title | old hash kept as obligation (`current`); new-title row asked with no note | — | Duplicate presentation (**excluded** by ROADMAP). The D-10 note (Pattern 6) is the only in-scope mitigation | excluded |
| — | real data: `iplayarr/.turingmind/state/format-53/*archived-2026-10-20-2` | 2 pass-1 `defer` (medium) → closed by recheck `resolved` on pass 2 | — | no real lost-decision case found; all fixtures are synthetic | — |

**Mechanism notes behind the verdicts** [VERIFIED: code read]:
- R1a re-hash: `score.py:2534-2538` recomputes the survivor's `stable_hash` from `best_decision["canonical_for_hash"]`, the orchestrator's per-pass HEAD read at the stored line. Only kept-open rows (`_kept_open_rows`, `score.py:404`) and NV rows (`score.py:2605-2616`) keep the stored hash verbatim. `templates/scoring.md:122` ("A carried row keeps its stored stable_hash verbatim") holds for those paths only. For a re-scored ordinary lead it holds only while the canonical is unchanged.
- R3 noise: `compute_score` adds +15 for `persisted`. `_corroborated_members` / the lone-lane ceiling (`LONE_LANE_BAND_CEILING = "warning"`) is released for the whole row by persistence (`score.py` comment "Persistence still releases it for the whole row"). On pass 1 a decided finding is `new`; on pass 2 it is `persisted`. The +20 `in_diff` term applies only when the finding's own line is in this pass's incremental diff (`05-state.md:65`: `$LAST_REVIEWED_SHA..HEAD`). Sweep results, unchanged code, lone lane, severity critical/high/medium: pass-2 line in diff → 15–17 of 17 decided findings changed band; pass-2 line not in diff → 4–6 of 10 changed (rises and drops).
- R4/R6: `carry_state._check_state` (`carry_state.py:247-281`) counts a member as a record only when it carries an `obligation` sidecar. `score.py` attaches one only to members that were once rows (`carried_obligations`, `score.py:2556-2558`). A fresh member that joins a decided row, or a pass-1 co-member, has no identity of its own.
- R5: member dedup (`score.py:2549-2559`) keys on `_finding_identity` = (agent, hash, line) and attaches the obligation only `if m is not best_member and id(m) in carried_obligations`. When the fresh duplicate sorts first, the carried twin is skipped as `seen`, and its obligation goes with it.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Locate a decided carried record at HEAD after a line shift | Orchestrator prose (`30-collect-score.md` step 0) | — | Only the orchestrator reads files; `score.py` is pure (no `os`/`pathlib`, AST-tested) |
| Know which carried records hold a current decision (to scope relocation) | `carry_state.py` (new read subcommand) | `05-state.md` binds the list | carry_state is the single closure/decision rule; prose never re-derives it |
| Detect "code next to the flagged line changed" | `score.py` (shared `_nearby_changed` helper used by `_independent_trigger` and the snapshot) | orchestrator supplies `changed_line_ranges` (already does) | one window definition for re-check and reopen (CONTEXT discretion) |
| Persist "reopened by nearby change" across passes | `score.py` `_snapshot_for` (snapshot key) | — | snapshot is the per-row scorer output that decision evidence copies |
| Decide current / stale, rise vs drop, coverage | `carry_state.py` `decision_state` / `stale_cause` | — | "extend here rather than adding a second comparator" (CONTEXT) |
| Write coverage + evidence at decision time | `carry_state.py record-decisions` (single writer) | — | single-writer rule |
| Keep a carried obligation through member dedup | `score.py` group/member loop | — | the dedup is where R5 loses it |
| Card note / reopen suffix wording | `batch_card.py` (`_row`, `_suffixes`) | `90-finalize.md` prose lock | helper renders; prose copies `card_text` verbatim |

## Standard Stack

No new libraries. The scripts are stdlib only, and two import sets are locked by tests: `carry_state.py` imports exactly `{json, os, sys}` (`TestImportSet`), and `score.py` may not import `os`, `pathlib`, `subprocess`, `shutil` or `glob` (`test_score.py:1480`) [VERIFIED: code read].

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.14.5 (local) | runtime for scripts/tests [VERIFIED: `python3 --version`] |
| pytest | 9.0.3 | test runner; bare `pytest` from `plugins/vibe-check/scripts` [VERIFIED: `pytest --version`] |
| unittest | stdlib | test classes are `unittest.TestCase` collected by pytest |

## Package Legitimacy Audit

No external packages are installed by this phase. Nothing to audit (slopcheck not run; not applicable).

## Architecture Patterns

### System Architecture Diagram (one review pass, decision path)

```
STATE_FILE (passes[], decisions{}) ──► 05-state.md: $CARRYFORWARD (open rows of last pass)
                                   └─► NEW: carry_state.py decided  ──► $DECIDED_HASHES
                                                                     │
HEAD files ──► 30-collect-score.md step 0: per carried row/member    ▼
               read canonical_line_content + canonical_window
               ├─ NV row ............ relocate by content (exists, Phase 53)
               ├─ NEW: decided row/member (hash ∈ $DECIDED_HASHES) .. relocate by content (same cases 1–3)
               └─ other ordinary .... stored-line read (unchanged)
                                   │
incremental diff ($LAST_REVIEWED_SHA..HEAD) ─► changed_line_ranges ──┐
                                   ▼                                 ▼
score.py run(): carry status ─► score ─► site grouping ─► members (+ NEW obligation-preserving dedup)
                                   │                         │
                                   └─► _snapshot_for(row) ◄── NEW _nearby_changed(record, ranges) → snapshot.nearby_at
                                   ▼
45-persist: passes[] += pass N (findings with snapshot, members[].obligation)
                                   ▼
Finalize: carry_state finalize-counts / batch_card rows
   decision_state(record):  evidence vs snapshot
     ordinary: file, canonical, nearby_at  (NEW: no `line`)  + band rule (NEW: drop keeps, rise reopens)
     NV:       unchanged (_NV_EVIDENCE_KEYS)
     NEW coverage: covered member that became a row → inherits; newcomer on decided row → asked
                                   ▼
   card: stale suffix with cause (code / nearby / severity-rise) + D-10 note ──► owner ──► record-decisions
                                                                                        (evidence + NEW covers)
```

### Component changes (where each fix lands)

| Fix | File(s) | Reproduced path |
|-----|---------|-----------------|
| F1 relocation for decided ordinary records | `phases/review/30-collect-score.md` step 0 (extend the NV block to "a carried record whose hash is in `$DECIDED_HASHES`"), `phases/review/05-state.md` (bind `$DECIDED_HASHES`), `carry_state.py` new read subcommand `decided` | R1a/b/c |
| F2 line-free ordinary evidence compare | `carry_state.py` `EVIDENCE_KEYS` compare set, `stale_cause`; `90-finalize.md:26` sentence | R1 |
| F3 nearby-change reopen | `score.py` extract `_nearby_changed` from `_independent_trigger`; `_snapshot_for` gains `nearby_at`; all snapshot writers (survivor `:2590`, kept-open `:406`, `_refreshed_obligation`); `carry_state` compares `nearby_at` | R2 |
| F4 direction-aware band | `carry_state.py` `decision_state`/`stale_cause` + a band-rank mirror of `score._BAND_SEVERITY` | R3b, R7 (and R3a per OQ1) |
| F5 coverage list | `carry_state.py record_decisions` writes `covers`; `_check_state`/`decision_state` honour it; `batch_card` D-10 note | R4, R6 |
| F6 obligation-preserving member dedup | `score.py` member loop `:2549-2559` | R5 |
| F7 card wording | `batch_card.py _suffixes`/`_row`; `90-finalize.md:101-106`; prose lock tests | R7, D-10, D-12 |

### Pattern 1: Decision follows a shifted line (F1 + F2)
**What:** Reuse Phase 53's NV relocation cases 1–3 (`30-collect-score.md:43-47`) for ordinary carried leads and obligation members whose hash has a current decision:
1. If the stored line still equals the stored first line, read there.
2. Otherwise use the unique (or uniquely nearest) match: set `line` there, and also on the matching `$RECHECK_REQUESTS` entry.
3. On a tie, keep the stored line, so the changed evidence is seen.
4. With no match, read the stored line as today. For an ordinary record a null canonical stays `fixed-since-last` (unlike NV).

Because the canonical text is unchanged, `score.py` recomputes the **same** `stable_hash`, so nothing moves in the frozen hash path. Then drop `line` from the ordinary evidence comparison in `carry_state` (`line` keeps being stored).
**Why line-free is safe:** two identical lines with one title already share one `stable_hash` and are deduplicated to ONE obligation in `carry_state._check_state` (`seen` set). Dropping `line` therefore adds no conflation that the hash does not already have [VERIFIED: `carry_state.py:274-281`]. NV made the same choice in Phase 53.
**Scope choice (recommended):** decided records only, not every ordinary carried record. Relocating every carried record would change live carry status for undecided findings (`needs-recheck` → `persisted`, +15, no recheck hint), which no reproduced failure here requires. Record the broader generalization as a carried idea. See Open Question 2.
**Example (target `carry_state` compare):**
```python
# carry_state.py — ordinary decisions compare on these; `line` stays stored, not compared
_ORDINARY_COMPARE = ("file", "canonical_line_content", "nearby_at")   # band handled by Pattern 3
```

### Pattern 2: One "nearby change" definition shared by re-check and reopen (F3)
**What:** Split the second half of `_independent_trigger` (`score.py:1325-1341`) into `_nearby_changed(record, changed_line_ranges)`: the pinned line plus `_NEARBY_LINES` (5) beneath, tested against this pass's ranges. `_independent_trigger` then calls it, so its behaviour is unchanged. Separately, for each carried record (lead, kept-open row, obligation member) where `_nearby_changed` is true this pass, `_snapshot_for` writes `nearby_at = pass_number` and a fresh `at_pass`. Otherwise it carries the prior `nearby_at` forward (absent stays absent). `carry_state` compares `nearby_at` with `evidence.get(k) == current.get(k)`, so legacy evidence without the key compares None == None.
**Why event-based is sound here:** `changed_line_ranges` is the incremental diff since the last reviewed SHA (`05-state.md:65`), which is exactly the change since the decision-time snapshot. Once stamped, `nearby_at` persists, so a reopen is not forgotten on a later quiet pass. After relocation (Pattern 1) the record's `line` is in HEAD coordinates, the same as the ranges.
**Window shape:** use Phase 56's literal 5-beneath window. Changing it to symmetric would also change Phase 56's re-check trigger, and the suite pins that behaviour (`TestReviewFix56`, m-series mutants). The probe showed an edit 2 lines ABOVE does not reopen today; under the 5-beneath rule that is the intended outcome.

### Pattern 3: Direction-aware severity (F4)
**What:** In `decision_state`, when the code keys match but the band differs: a lower-ranked band than `evidence.band` returns `"current"` (D-06), and a higher-ranked band returns `"stale"` with cause `"severity"` (D-05). Ranks mirror `score._BAND_SEVERITY` = {critical 4, warning 3, medium 2, low 1}. `carry_state` cannot import `score`, so add a cross-module equality test. The NV band keeps today's rule (D-04: any band change re-asks; an NV row does not rise or drop within the order). Defer and dismiss are handled identically (D-07): the comparison ignores the decision kind.
**Pending owner ruling (Open Question 1):** a literal "every rise reopens" keeps R3a. Most lone-lane findings decided on pass 1 rise one band on pass 2 from persistence alone. The recommended narrowing: a rise reopens only when the row gained a reviewer lane not present at decision time. That needs `attribution` saved on the decision record by `record-decisions`, and the card can then say why: "rose from warning to critical: security now also reports it". A legacy record without saved attribution falls back to "any rise reopens".

### Pattern 4: Coverage recorded at decision time (F5)
**What:** `record_decisions` stores `covers`: the `(agent, file, title)` of every member on the decided row at decision time, the lead included. This new key is written only by the single writer, and older records are never rewritten. Then:
- **Newcomer (D-08, R4):** a row with a current decision that now holds a member whose identity is not in `covers`, and that member has no obligation of its own. The row stops counting as closed for that member. Recommended: the row reopens with cause `"joined"` and a D-10 note.
- **Split (D-09, R6):** an open record with no decision of its own whose `(agent, file, title)` is in a decision's `covers` inherits that decision while its own evidence is unchanged. Its code evidence is checked with the same file / canonical / nearby rule.
- **Legacy:** decisions without `covers` keep today's behaviour. This follows the locked rule: legacy decisions keep closing as before.

**Identity choice:** `(agent, file, title)` is already the cross-pass identity `05-state.md:62` uses to anchor `$TOUCHED_PATHS` ("the hash cannot anchor it; file + agent + title can"). `successor_links` uses `(file, title)`. Do not key coverage on a member's computed `stable_hash`: member refs carry no `canonical_line_content` (excluded from `MEMBER_KEYS`, `score.py:269`), and a hash rebuilt from `current_code`'s first line can differ from the HEAD-read hash `score.py` assigns when the member later becomes a row.
**Rule change to state explicitly:** today `carry_state` says "Closure is evaluated per record and is never inherited from a lead." D-09 deliberately adds ONE inheritance path: explicit coverage recorded at decision time. It must never come from whichever lead is current now. Update the module docstring "WHAT CLOSES", `90-finalize.md:25-26`, and add a mutant test for it.

### Pattern 5: Member dedup never drops a carried obligation (F6)
**What:** In the member loop (`score.py:2549-2559`), when an occurrence identity is already `seen` and the skipped record is in `carried_obligations`, attach its obligation to the kept ref for that identity, unless that ref is the row's own lead with the same hash. The decided record then stays an open record under its own hash.
**Note:** this is the exact residual Phase 46 accepted (`46-CONTEXT.md:136`). The owner rule allows it now because it is a reproduced obligation loss.

### Pattern 6: Card wording (F7, D-10/D-12)
Extend `_suffixes` with cause-specific text, keeping today's `(was: dismissed — reason)` tail:
- `nearby` — " — code next to it changed since your decision on pass N (was: …)"
- `severity` rise — " — severity rose (A → B) since your decision on pass N[: <lane> now also reports it] (was: …)"
- `joined` (D-10) — " — 1 finding here already dismissed (your reason: …); asking only about the new one"

The CONTEXT example "You dismissed this on pass 4 ('false positive, guarded upstream'). Reopened: code next to it changed." is a wording target. Keep the suffix form so the compact-card budget and existing tests survive. Each new phrase gets a `*_holds(text)` prose lock plus one removal mutant (pattern in `test_finalize_card.py:254-306`, `test_card_text.py:89`). Phase 58 owns broader recovery wording, so do not touch other cards.

### Anti-Patterns to Avoid
- **Changing `stable_hash` inputs or adding `line` to the hash.** That orphans every persisted dismissal, and GOLDEN_DIGEST `7a516d01…` is frozen (`test_score.py:43`).
- **A second comparator.** All currency logic goes through `decision_state` / `stale_cause` (CONTEXT).
- **Rewriting existing decision records** to add `covers` or `attribution`. Only new writes carry them.
- **Forgetting the `nearby_at` carry-forward in `_snapshot_for`'s keep rule.** If dropped, evidence holds `nearby_at=2` while the next snapshot has none, and the finding is re-asked forever.
- **Broad relocation of all carried rows** without a reproduced need (Phase 40 lesson: rewrite breadth introduced 12 new findings).
- **Treating band noise as evidence** (R3a). Do not ship "every rise reopens" without the owner's ruling.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relocating a record by content | a new search rule | `30-collect-score.md` NV cases 1–3 (unique / nearest-unique / tie keeps stored line) | already reviewed through Phase 53's adversarial passes; same tie semantics |
| "Code near the line changed" | a new window | `_independent_trigger`'s window, split out as a shared helper (`_NEARBY_LINES = 5`) | CONTEXT requires one definition shared with re-check |
| Linking an edited (re-hashed) finding to its decision | new linking | `batch_card.successor_links` | exists; annotation only, never closes |
| Band ordering | ad-hoc string compares | mirror of `score._BAND_SEVERITY` + equality test | carry_state cannot import score |
| Multi-pass pipeline tests | bespoke JSON fixtures | `test_carry_state.append_pass`, `decide`, `e2e_gate`; `test_score._hl/_ko_find/_carried/_ko_next_cf/_hl_env/_p45_recheck`; `ab_pipeline` (`test_carry_state.py:1829`) | real scorer → state → gate chain, as Phase 56 used |
| Mutation tests | hand-checked guards | `TestIndependentRouteMutants` pattern (source text replace + re-import, `test_verified_fixes.py`) | proves each guard can trip |

## Persisted State Compatibility (in place of a rename inventory)

| Category | Finding | Action |
|----------|---------|--------|
| Stored data | Root `decisions` records in users' `.turingmind/state/format-53/*.json`. The owner's real files hold 10 evidence-bound records, none with `covers`. | Code only. New keys are written on new decisions; old records are read under legacy rules. No data migration. |
| Snapshot shape | `snapshot` inner keys are not validated by `state_shape` (only finding keys are; `future-schema.json` `finding_optional` already lists `snapshot`) [VERIFIED: state_shape.py grep]. Adding `nearby_at` needs no schema change. | Add a rollback note: a pre-57 scorer rebuilds the snapshot without `nearby_at` (drops it), and a pre-57 reader ignores `covers` and compares `line`, so it re-asks. That fails toward asking, never toward silent closure. |
| Decision record shape | `decisions` values are free-form objects to `state_shape`; carry_state validates only on its own reads. | Document `covers` / `attribution` in the carry_state docstring and `ROLLBACK` section. |
| Live service config / OS state / secrets | None. Local plugin scripts only. | none |
| Installed plugin cache | Agents and prose run from the installed cache, not the repo (memory: "vibe-check agent install sync", "Install chronically stale"). | Only matters for a live check. Phase 57 verification is local tests, so no cache resync is needed unless a live run is approved. |

## Common Pitfalls

### Pitfall 1: Existing tests encode the behaviour D-01/D-06 change
**What goes wrong:** `test_carry_state.py::TestDecisionEvidence::test_line_move_reopens` (`:1283`), `test_batch_card.py::test_rows_stale_line_move_cause_code` (`:143`), and the rollback table rows `("line move", line_move_state)` (`:1469`) assert that a line move re-asks.
**How to avoid:** change them deliberately in the same commit as the fix, with a note that cites D-01. Never delete them silently. `band_change_state` (medium → warning, a rise) stays valid under D-05. Add a new drop fixture.

### Pitfall 2: Band noise masks code-path fixtures
**What goes wrong:** a fixture that should prove "kept" fails because the band rose through persistence (R3a), not because of the code path under test.
**How to avoid:** for code-path fixtures, use band-stable inputs (conf 70, pass-2 ranges that exclude the flagged line), or assert `stale_cause`, not just counts. Assert the fixture's band on both passes, per the "assert fixtures contain what you think" rule.

### Pitfall 3: The obligation/hash path differs for above- and below-threshold rows
**What goes wrong:** R1 shows two different failure shapes: a re-hash when the row is above threshold, and a kept-open stale row when it is below.
**How to avoid:** cover both in the RED fixtures (R1a and R1b).

### Pitfall 4: Relocation must also move the recheck request line
**What goes wrong:** a relocated record whose `$RECHECK_REQUESTS` entry still names the old line is rejected as `verdict: record not carried` (`30-collect-score.md:45`).
**How to avoid:** keep that clause in the extended prose and lock it in the prose test.

### Pitfall 5: `nearby_at` and kept-open / obligation snapshots
**What goes wrong:** `_kept_open_rows` and `_refreshed_obligation` rebuild snapshots from a `basis` dict. If `nearby_at` is not threaded through them, members and kept-open rows never reopen, or they lose the key and re-ask forever.
**How to avoid:** write one test per snapshot writer, each with a mutant.

### Pitfall 6: Coverage must not swallow a later concern
**What goes wrong:** D-08 says a decision "never silently covers a different reviewer's new concern".
**How to avoid:** `covers` is frozen at decision time. Only a NEW decision record (via `record-decisions`, with history) extends it. A test should prove a newcomer is asked even when its band is lower than the lead's (R4 exactly).

### Pitfall 7: `--all` mode and empty diffs
**What goes wrong:** `--all` and the carry-forward-only path (`05-state.md` step 5, empty incremental diff) have no `changed_line_ranges`, so a nearby change can never be seen there. That matches Phase 56's re-check trigger.
**How to avoid:** document it as a known limitation and do not invent a fingerprint read.

### Pitfall 8: Replay gate
**What goes wrong:** score.py changes (F3, F6) may move archived replay output.
**How to avoid:** run the Phase 56 gates. `replay.py candidate … --scorer rev:HEAD` must show REGRESSED 0. `replay.py diff --base rev:24c0c00 --scorer rev:HEAD --roots all --allow ../../../docs/design/b3-ground-truth/ALLOWANCES-phase53-nv.json` must show 0 differing [CITED: 56-06-SUMMARY.md:76-77]. If `nearby_at` appears in replayed snapshots, an allowances entry is a recorded decision, not a silent waiver.

## Code Examples

### RED fixture skeleton (from the probe; Wave 0 converts each R-row into one of these)
```python
# Source: probe57.py, built on test_carry_state.append_pass + score.run (real chain)
def test_r1_line_shift_keeps_decision(self):
    L0 = base_file()                                   # 60 distinct lines
    s1, hA = pass1_decided(L0, conf=70)                # warning, dismissed at pass 1
    L1 = ["inserted_%d = 0" % i for i in range(3)] + L0
    s2 = run_pass(s1, L1, findings=[], n=2, ranges={F: [[1, 3]]})
    rec = record_of(s2, hA)                            # same hash, relocated to line 13
    self.assertEqual(rec["line"], 13)
    self.assertEqual(carry_state.decision_state(rec, s2), "current")
    self.assertEqual(e2e_gate(s2, {}), "write")
```
For R1 the orchestrator's relocation is prose, so the fixture's `next_cf` simulator must apply the relocation rule. The prose itself is locked separately by a `*_holds` test. Name this split explicitly in the plan, so the fixture does not quietly test a simulator the shipped prose never follows.

### Current comparator (the single point to extend)
```python
# Source: plugins/vibe-check/scripts/carry_state.py:457-482 (decision_state)
keys = _evidence_keys(evidence, record)
current = _evidence_of(record, nv=keys is _NV_EVIDENCE_KEYS)
if all(k in evidence and evidence[k] == current[k] for k in keys):
    return "current"
return "stale"
```

### Test commands
```bash
cd /Users/julianamacbook/turingmind-code-review/plugins/vibe-check/scripts
pytest -q test_carry_state.py test_batch_card.py test_card_text.py      # ~6 s
pytest -q test_verified_fixes.py test_score.py -k "KeptOpen or HLane or Independent"
pytest -q                                                                # full suite, ~4.5 min
```

## State of the Art (in this codebase)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Decided hash closes unconditionally | evidence-bound decisions (4 keys) | v2.11 Phase 47 | line shift and any band move re-ask (R1, R3) |
| NV read at stored line | NV relocation by content + `_NV_EVIDENCE_KEYS` (no line) | v2.12 Phase 53 | the template for Pattern 1 |
| Absorbed rows lose identity | `members[].obligation` sidecars for once-rows | v2.11 Phase 46 | newcomers and pass-1 co-members still have no identity (R4, R6); dedup residual (R5) accepted then |
| — | nearby-change trigger for independent re-check | v2.13 Phase 56 | the window Pattern 2 shares |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The owner's D-05 ("a rise reopens") did not anticipate that persistence alone raises most pass-1 decisions one band on pass 2 | Open Question 1, Pattern 3 | If the owner does want every rise re-asked, the "lane gained" narrowing is wrong. Literal D-05 is then a one-line rule, but the owner will see repeat severity questions on most rows |
| A2 | Agents in an incremental pass usually do NOT re-report an unchanged finding whose line only shifted (they review the diff), so R1a/b (no re-report) is the common real shape | Reproduction R1 | If they usually do re-report, R1c (duplicate rows) is the common shape. Pattern 1 fixes both either way |
| A3 | `(agent, file, title)` is stable enough across passes to key coverage | Pattern 4 | An LLM title drift on the same lane breaks coverage inheritance on split. The finding is then asked again, the failure direction the owner rules allow (ask, not silently close) |
| A4 | Restricting relocation to decided records is preferable to relocating all carried records | Pattern 1, OQ2 | The broader version may be wanted later. It is recorded as carried, not built |

## Open Questions

1. **Which severity rises should reopen a decision? (Product. Needs the owner.)**
   - What we know: under today's scoring, a finding decided on pass 1 usually comes back on pass 2 one band higher (warning → critical) with no code change. The +15 "persisted" bonus and the lone-reviewer cap lifting cause this (R3a sweep). Applied literally, D-05 would keep asking the owner about these rows.
   - Options for the owner, in plain terms: (a) every rise re-asks (simple; most decided rows come back once); (b) **recommended:** a rise re-asks only when another reviewer now also reports it (the card names that reviewer). A rise from the finding merely surviving another pass keeps the decision.
   - Recommendation: the planner adds a decision checkpoint, or the orchestrator asks before execution. Build (b) if it is approved. Either way the drop rule (D-06) and its fixture proceed.
2. **Relocate only decided records, or every carried ordinary record?** (Technical, Claude's call.) Recommend decided-only, as the narrowest fix for the reproduced failure. Record "general ordinary relocation" as a carried idea with its evidence (the phantom wrong-line rows in R1a/R1c also affect undecided findings).
3. **D-08 newcomer UX: reopen the whole decided row, or ask only the newcomer as its own card row?** The coverage list supports either. Reopening the row with the D-10 note keeps one hash and no new identity machinery. Asking only the newcomer needs a stable hash for a member that was never a row, which `score.py` does not produce today. Recommend reopening the row with the note, since the owner's D-10 note wording fits that shape. This is presentation, so the planner may decide.
4. **Members present on the row at pass-1 decision time are not listed on the finalize card** (`card_text` shows the lead title only). D-09 treats them as "covered". If the owner considers them unseen, D-09 would instead require asking them at decision time, which is a larger change. Recommend following D-09 as written (covered), and adding member titles to the D-10 note only.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | all scripts/tests | ✓ | 3.14.5 | — |
| pytest | suite | ✓ | 9.0.3 | — |
| git | branch/commits | ✓ | — | — |
| replay.py archives (`docs/design/b3-ground-truth/…`) | replay gate | ✓ (used by Phase 56) | — | — |
| Model/API access | none (no paid runs) | not needed | — | — |

Note: a broad `find` under the home directory is blocked by the v2.12 holdout guard hook. Probes must stay inside the repo, the scratchpad and the named iPlayarr state path.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 Auth/Session/Access | no | — |
| V5 Input Validation | yes | carried and finding text is attacker-influenced. `score.py` strips `snapshot`/`members`/`status`/`recheck_settled` from fresh findings at ingress (`score.py:2133-2141`). **`nearby_at` must be added to that scrub list**, because a forged value could suppress or force a reopen. `covers`/`attribution` come only from the state through `record-decisions`, never from the owner payload (validate the payload key set exactly as `_DECISION_ENTRY_KEYS` does) |
| V6 Cryptography | no (sha256 identity unchanged) | — |
| V7 Errors/Logging | yes | REASONS lines never include a hash, title, path or owner text. Card text is flattened DATA (`_one_line`) |

| Threat | STRIDE | Mitigation |
|--------|--------|------------|
| Agent forges `snapshot.nearby_at` or an older `at_pass` to suppress a reopen | Tampering | ingress scrub (above) + a mutant test |
| Crafted title collides into a `covers` identity to inherit a dismissal | Spoofing | coverage requires the same agent (dispatch identity, not self-claimed) + file + title, AND the record's own code evidence must match. Inheritance never applies across files |
| Relocation picks a lookalike line to keep a dismissal on changed code | Tampering | ties keep the stored line (Phase 53 case 3); relocation applies only to records with a current decision; nearby-change still reopens |

## Sources

### Primary (HIGH confidence, read or run in this session)
- `plugins/vibe-check/scripts/carry_state.py` (docstring, `_check_state`, `decision_state`, `stale_cause`, `record_decisions`)
- `plugins/vibe-check/scripts/score.py` (`_snapshot_for`, `_kept_open_rows`, `stable_hash`, `_finding_identity`, `_expand_members`, `_independent_trigger`, carry loop, grouping/member loop, NV rows, ingress scrub)
- `plugins/vibe-check/scripts/batch_card.py` (`build_rows`, `successor_links`, `_suffixes`)
- `plugins/vibe-check/phases/review/30-collect-score.md` step 0; `05-state.md` (incremental diff, `$TOUCHED_PATHS`); `phases/shared/90-finalize.md:15-125`
- `fixtures/future-schema.json`, `state_shape.py`
- Local probe runs (`probe57.py` and inline variants) on HEAD 9be39a8
- Real state: `/Users/julianamacbook/iplayarr/.turingmind/state/` (all files and `format-53/`)
- `.planning/phases/56-verified-fixes-close/56-VERIFICATION.md`, `56-REVIEW-FIX.md`, `56-06-SUMMARY.md`
- `.planning/milestones/v2.11-phases/46-carry-forward-integrity/46-CONTEXT.md:136` (accepted residuals)

### Secondary / Tertiary
- None. No web sources were needed: this is an internal codebase domain.

## Metadata

**Confidence breakdown:**
- Reproduction verdicts: HIGH. Each one was executed on current code through the real scorer and helper chain.
- Architecture / mechanisms: MEDIUM. Designed from code reads; mutant and replay behaviour is not yet proven.
- Pitfalls: HIGH for 1–5 and 8 (observed or cited); MEDIUM for 6–7.

**Research date:** 2026-10-25
**Valid until:** until the next change to `score.py` / `carry_state.py` / `30-collect-score.md` on this branch (the code moves fast; re-run the probe if HEAD moves past 9be39a8 on those files).
