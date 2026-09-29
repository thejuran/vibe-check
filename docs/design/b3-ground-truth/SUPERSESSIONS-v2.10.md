# Supersessions — v2.10 sealed evidence

Recorded supersession decisions over the sealed v2.10 evidence chain. A sealed statement is NEVER
rewritten: it is quoted verbatim here beside the decision that supersedes it, so a later reader sees
both sides of the record at once. `PREREGISTRATION-v2.10.md` is never touched at all — its
staged-seal rule allows no further edit — and `SCORING-v2.10.md`, `RESULTS-v2.10.md` and
`RUN-METHOD-NOTES-v2.10.md` carry only a one-line pointer back to this file. Phase 43 reads this
ledger and reports against BOTH the sealed literal denominators and the superseded ones.

## Rules

- This file is APPEND-ONLY. Entries are numbered `## NNN — <date> — <title>`, appended at EOF in
  order, and never edited once committed.
- Entries in this ledger are never reverted. A correction is a new entry citing the one it corrects;
  the commits that create and extend this ledger sit outside every batch rollback unit (Phase 40
  plan 40-06 records those units explicitly).
- Every entry carries the same four labelled blocks, in this order:
  `**Sealed statement (verbatim, unchanged):**`, `**Evidence:**`, `**Effect:**`, `**Sign-off:**`.
- Field labels that also exist as machine-read bare `key: value` lines (for example the verifier pin
  labels) are backticked wherever they appear in prose, so exactly one column-0 pin pair exists in
  this file and an anchored grep stays single-valued.

## 001 — 2026-09-08 — should-quiet-7 excluded from the quiet set (D-01)

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/diffs/should-quiet-7.provenance`:

> This is defect-free feature code — reviewing it should produce NO critical/warning finding.

From `plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md` (per-diff should-quiet table), quoted as
raw bytes so the sealed row is reproduced exactly:

```
| 12 | should-quiet-7 | new | settings input-parse path — bounded `safe_float` mirroring the adjacent `safe_int` | FP, FP, FP | **3/3 FP** |
```

From the sealed SEAL2 blob of `PREREGISTRATION-v2.10.md`: `DENOM_QUIET_RUNS: 21`.

**Evidence:**

Verified in the triggarr clone. The reviewed commit `05cfd1b` adds a POST parser reading
`form.get("shutdown_drain_timeout")`, but the template input that supplies that form field landed
in the LATER commit `dbc3dcb`. `shutdown_drain_timeout` was already a persisted `GeneralConfig`
setting accepting non-default values before `05cfd1b`. So at the reviewed state the field is absent
from the submitted form, `form.get` yields nothing, and the bounded parse falls back to its default
— every settings save silently resets a configured value to 60.0. That is a real
configuration-loss defect, so the fixture's provenance claim is wrong and its three baseline
"FPs" were correct catches.

**Effect:**

- The quiet set becomes 6 diffs / 18 runs; the superseded baseline false-positive rate is **16/18**.
- The sealed headline **19/21** stays visible everywhere it was recorded, marked superseded with a
  pointer to this entry. No sealed number is rewritten.
- Phase 43 runs the **11-diff** set and reports against BOTH the sealed literal denominators and the
  superseded ones.
- The diff is NOT relabeled should-catch: it is a forward diff, and the sourcing rules require
  reversed-fix should-catches.
- The diff is NOT replaced: no new sealing or baseline runs happen mid-window.

**Sign-off:** owner, 2026-09-08, discuss-phase decision D-01.

## 002 — 2026-09-08 — session-rotation SITE judged in run-tree coordinates (D-03a)

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/SCORING-v2.10.md` §3.4, the SITE declaration for
`triggarr-session-rotation`:

```
SITE `triggarr/web/routes.py` : 1445-1451 / 1459-1469 (planted hunks; findings land at 1564-1588 in the run tree)
```

**Evidence:**

1445-1451 / 1459-1469 are PATCH coordinates. The hunks, once applied to the run tree at run HEAD
`f4366a2`, land at 1564-1588 — which SCORING §3.4 already states parenthetically, and which the
three recorded winning findings match (L1564, L1567, L1571).

**Effect:**

- SITE for this diff is judged in run-tree coordinates of the APPLIED hunks, not in patch
  coordinates. The recorded **3/3 catch** for `triggarr-session-rotation` stands unchanged.
- The rule applies to every later scoring of this diff, including the Phase-40 spot-checks and
  Phase 43.

**Sign-off:** owner, 2026-09-08, discuss-phase decision D-03(a).

## 003 — 2026-09-08 — Phase 43 pins exactly fable 5.1 (D-03b)

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/RUN-METHOD-NOTES-v2.10.md` §"Harness pin": `pin-model: fable 5`.

**Evidence:**

The pinned value `fable 5` is a family+generation pin, matched loosely enough that any `fable 5.x`
normalizes onto it. Every one of the 12 Phase-38 session fingerprints in fact recorded
`model: Fable 5.1`, which normalizes to `fable 5.1`.

**Effect:**

- The Phase 43 harness tuple requires EXACT equality with `fable 5.1`, not the substring-loose
  `fable 5`. A `fable 5.2` session is harness drift and is not silently aggregated.
- The Phase-38 cohort is unaffected: all 12 fingerprints already normalize to `fable 5.1`.
- The `RUN-METHOD-NOTES-v2.10.md` pin lines are NOT edited — correcting them is illegal once
  fingerprints exist. Phase 43's checklist reads this entry instead.

**Sign-off:** owner, 2026-09-08, discuss-phase decision D-03(b).

## 004 — 2026-09-08 — seal verifier hardened and re-pinned (D-04)

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/RUN-METHOD-NOTES-v2.10.md` §"Seal verifier pin", the Phase-38 pin
pair (quoted, not re-declared): `verifier-commit: a407539115872137dc55d99aef439a9c5a4f16d9` and
`verifier-sha256: 7be8ed39e9ad38a521caa17316fcea8894a7f25ab54b72af7b673a9bff75daaf`, with the
consumer rule:

> Every consumer of the seal check first asserts the live verifier file's sha256 equals
> verifier-sha256 AND that exactly one commit ever touched the path, then executes the
> check via `git show <verifier-commit>:<path> | python3 -` — the pinned blob, never the
> working file.

**Evidence:**

The Phase-38 derivation was `git rev-list --reverse HEAD -- <manifest>`, which is branch-relative
and history-simplified: it walks only HEAD's first-parent-visible history and drops commits whose
change was discarded by a merge. Both properties are exploitable. A third manifest edit made on a
side branch and merged with `-s ours` leaves HEAD's content identical and still counts 2 under
`rev-list HEAD` — the check is defeated while a real third edit exists in history.

Six scratch-repo scenarios were run against the hardened file (git 2.54.0, 2026-09-08):

1. **legal pair** — seal-1 commit, then a pure five-line whitelisted append →
   **OK** (`SEAL2-APPEND-WHITELIST-OK`, exit 0).
2. **tampered** — seal-2 also changed one seal-1 byte →
   **FAIL**, `SEAL-2 MODIFIED THE SEALED BAR (not a byte-pure append)`.
3. **CRLF** — seal-1 LF endings rewritten to CRLF before the append →
   **FAIL**, `SEAL-2 MODIFIED THE SEALED BAR (not a byte-pure append)`.
4. **legal `--no-ff` merge** of a feature branch into main after seal-2 → **OK**, exactly 2 revs.
   (The `--full-history` form without `--simplify-merges` counts 3 here and fails a legitimate
   publish merge.)
5. **evil `-s ours`** — a third manifest edit on a side branch merged with `-s ours`, HEAD content
   unchanged → **FAIL**, `manifest commits != 2` (4 revs). The old `rev-list HEAD` form counted 2
   and passed this.
6. **unmerged side-branch edit** of the manifest → **FAIL**, `manifest commits != 2` (3 revs). The
   old form counted 2 and passed this.

**Effect:**

- Derivation is now the following, which must yield exactly 2:

  ```
  git log --format=%H --full-history --simplify-merges --topo-order --reverse --branches --tags --remotes -- <manifest>
  ```

  `--simplify-merges` keeps a legitimate `--no-ff` publish merge from counting;
  `--branches --tags --remotes` reaches side branches. `--all` is deliberately NOT used, because it
  also walks `refs/stash` (fail-closed but confusing).
- Three `git merge-base --is-ancestor` asserts bind the derived pair to the tree being scored:
  SEAL1 → SEAL2, SEAL1 → HEAD, SEAL2 → HEAD. A seal pair that exists only on an unmerged
  branch now fails with `ancestry broken`.
- New consumer rule, replacing the "exactly one commit ever touched the path" clause quoted above:
  the verifier path's full-history all-ref commit count is **2** (the Phase-38 pin commit `a407539`
  plus the hardening commit), and the SECOND of those commits must equal the `verifier-commit` value
  pinned below. Execute the check the same way as before, against the pinned blob:

  ```
  git show <verifier-commit>:docs/design/b3-ground-truth/verify-seal2-append.py | python3 - <repo>
  ```
- The Phase-38 record stands as written: it recorded what was true at scoring time, and the
  pinned old blob is still re-derivable:

  ```
  git show a407539:docs/design/b3-ground-truth/verify-seal2-append.py
  ```

The current pin — the only two column-0 pin lines in this file:

verifier-commit: de8633cb3e1a295208d89f5be7472e665aec7822
verifier-sha256: 605e61a3deee6894ef4d30a1869d944d3685645749c601dacbefb81573d081a3

**Sign-off:** owner decision recorded in discuss-phase (D-04), executed 2026-09-08.

## 005 — 2026-09-24 — Phase-40 spot-check sensitivity pair selected (triggarr-secret-in-logs, should-quiet-5)

This entry registers a RULE for the Phase-40 spot-checks. It supersedes no sealed number and moves
no denominator: every figure quoted below stands exactly as sealed.

**Sealed statement (verbatim, unchanged):**

From `plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md` (per-diff tables), quoted as raw bytes:

```
| 1 | triggarr-secret-in-logs | carried | secret/API-key/PII leaked into logs (NOT "log formatting") | warning | catch, catch, catch | **3/3** |
| 10 | should-quiet-5 | new | log-sanitization / secret-handling — wraps file-name interpolation in `sanitize_log_value` | clean, FP, clean | **1/3 FP** |
```

**Evidence:**

- `triggarr-secret-in-logs` has the LEAST HEADROOM of any should-catch diff. Per `SCORING-v2.10.md`
  §3.1, the winning finding in all three baseline runs was `codex-adversarial` (critical 100 / 99 /
  96), and the best NATIVE finding cleared the warning floor (80) by the smallest margin in the set:
  `impact` warning 82 in run 1 (`bugs` 72 was sub-floor), 88 in run 2, 85 in run 3. Being
  codex-led, it also directly exercises the Family-3 extraction (40-04) and the deep-review Phase-3
  rewrite (40-11).
- `should-quiet-5` is the ONLY should-quiet diff not at 3/3 FP: clean, FP, clean (`SCORING-v2.10.md`
  §4.5). Its single FP is the "out-of-diff reach" class — `impact` warning 92 on a neighbouring
  test file, not the diff's own lines — which is exactly the in_diff / reviewed-set prose 40-08
  rewrites. It is the quiet diff most likely to flip in either direction.
- Not selected, with reasons:
  - `triggarr-autoescape` — runner-up. The only should-catch with a historical miss (v2.9: 2/3),
    but its native winners sit at 82-92, more headroom than secret-in-logs.
  - `should-quiet-6` — the most STABLE FP in the set (byte-identical codex title at critical/100
    in all three runs). It cannot get worse, so it carries no signal.
  - `should-quiet-7` — excluded from the quiet set by entry 001.

**Effect:**

- The D-05 per-batch ×1 checks and the end-of-phase ×3 check run on this pair and no other.
  Catch-rate-no-worse is judged on `triggarr-secret-in-logs` holding 3/3 at phase end; the
  `should-quiet-5` FP count is judged against its own 1/3 triplet at ×3 and is informational at ×1.
  The runbook is `docs/design/b3-ground-truth/SPOT-CHECK-v2.10-phase40.md`.
- Phase-40 sessions are fingerprinted in `RUN-METHOD-NOTES-phase40.md`.
  `RUN-METHOD-NOTES-v2.10.md` receives nothing beyond the single pointer line entry 004 already
  added: Phase-38 scoring walks that file for its own session binding (F15).
- The sealed-baseline integrity assert is the git TREE of `docs/design/b3-ground-truth/runs-v2.10`,
  `82c412b6e58b5d5a1dbddca0239f0f4b26833b4a`. The earlier commit-based form (`633f1dd`) predates
  the archives and would fail on intact evidence (F12).

**Sign-off:** owner decision D-05 recorded in discuss-phase (spot-check sizing and pair), selection
executed from the sealed evidence 2026-09-24.

## 006 — 2026-09-24 — Phase-40 harness pin corrected: `pin-claude-code` 2.1.261 → 2.1.281 (owner decision)

This entry records a PIN CORRECTION for the Phase-40 spot-checks. It supersedes no sealed number and
moves no denominator. The Phase-38 pin in `RUN-METHOD-NOTES-v2.10.md` is untouched; only the
Phase-40 copy in `RUN-METHOD-NOTES-phase40.md` changes, inside the correction window that file
defines for itself (zero session blocks, zero run commits under `runs-v2.10-phase40/`).

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/RUN-METHOD-NOTES-v2.10.md` (the Phase-38 harness pin, carried into
`RUN-METHOD-NOTES-phase40.md` byte-for-byte by plan 40-09), quoted as raw bytes:

```
pin-claude-code: 2.1.261 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: fable 5
```

**Evidence:**

- On 2026-09-24 `claude --version` on the owner's machine printed `2.1.281 (Claude Code)`;
  `codex --version` printed `codex-cli 0.153.4`, matching its pin. The pinned CLI 2.1.261 is no
  longer installed. Plan 40-09 recorded this drift at authoring and left the decision to the owner.
- At the time of this correction `RUN-METHOD-NOTES-phase40.md` held zero `## Harness fingerprint`
  session blocks and `runs-v2.10-phase40/` held only `PLAN-COMMITS.json` (plan identity records, no
  run evidence), so the file's own rule permits the correction.
- The alternative, downgrading Claude Code to 2.1.261 and holding it there for every Phase-40
  session across days, was put to the owner and declined.

**Effect:**

- `RUN-METHOD-NOTES-phase40.md` now carries `pin-claude-code: 2.1.281 (Claude Code)`. The STEP 0.25
  fingerprint block accepts 2.1.281 sessions and still stops on any further drift.
- Every Phase-40 spot-check compared against the sealed Phase-38 baseline (measured on 2.1.261)
  carries the Claude Code version as a NAMED CONFOUND: a movement on the sensitivity pair has two
  candidate causes, the Phase-40 change under test and the newer CLI. The per-batch ×1 checks remain
  the guardrail D-05 sized them as; the proof is Phase 43's full re-measure (entry 003 pins exactly
  `fable 5.1` there).
- `pin-codex` and `pin-model` are unchanged. `RUN-METHOD-NOTES-v2.10.md` receives nothing.

**Sign-off:** owner decision 2026-09-24, taken before batch 1 in the milestone-orchestrator session,
recorded by the assistant.

## 007 — 2026-09-29 — a collapsed H-LANE row's member titles satisfy AXIS (D-14, Phase 41)

This entry registers a RULE for scoring a site that the Phase-41 H-LANE grouping collapses into one
row. It supersedes no sealed number and moves no denominator: every figure quoted below stands
exactly as sealed, and the three-gate rule itself is unchanged.

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/SCORING-v2.10.md` §3 preamble, lines 279-282 (the sentence ends
mid-line 282), quoted as raw bytes:

```
A **catch** requires SITE (right file + within the planted hunk, keyed to the row's base_sha) AND
AXIS (the finding names the key's required MECHANISM, honoring the row's NOT-clause) AND BAND
(rendered band ≥ the row's floor). SITE-only, or SITE+AXIS-below-band, = `detected-below-threshold`
= a MISS in the headline.
```

From `docs/design/b3-ground-truth/ANSWER-KEY-b3.md` lines 5-6 (the scoring-input rule; the sentence
begins on line 5 and ends on line 6), quoted as raw bytes:

```
Scoring input: `state.passes[-1].findings[]` from the archived per-run
`runs/<diff-id>/run-<n>/state.json` (D-06 — never the chat transcript).
```

From `docs/design/b3-ground-truth/ANSWER-KEY-b3.md` lines 31-32 (the AXIS gate), quoted as raw
bytes:

```
2. **AXIS** — the finding's `title` (+ `category` as corroboration) names the defect
   MECHANISM in the row's AXIS column — not merely a defect at the right location.
```

**Evidence:**

- H-LANE (Phase 41, D-03) collapses every same-site finding across domains into ONE surviving row,
  led by the strongest lane. Scores clamp at 100, so at most catch sites several lanes tie and the
  lead is effectively picked by the `stable_hash` tie-break, not by which title names the defect
  (`41-RESEARCH.md` Pitfall 1).
- In 12-14 of the 26 protected catch runs the lead title names a different axis. The two exemplars:
  on `triggarr-autoescape`, `codex-adversarial` "Deprecated template env options can break startup
  when warnings are fatal" (`runs/triggarr-autoescape/run-2`), which the autoescape NOT-clause
  excludes; on `triggarr-secret-in-logs`, `compliance` "Raw exception logged instead of sanitized
  summary, bypassing established _sanitize_exc convention"
  (`runs-v2.10-phase40/final/triggarr-secret-in-logs/run-2`), a convention framing that names no
  leak. Under a lead-title-only reading Phase 43 would score those runs `detected-below-threshold`.
- The catch finding is NOT lost. It is a member of the surviving row, and it is recorded in
  `filtered[]` as `absorbed-into: <hash>` (the Fable-A2 mechanism), where the scoring input above
  never looks.
- Rejected alternatives (CONTEXT D-14): collapse-in-report-only, which widens the phase into the
  prose renderer; and lead-title-only, under which H-LANE fails the zero-regression guardrail on
  the affected catch runs.
- Every finding at SITE in the 29 archived catch runs is pre-adjudicated for AXIS, with the
  deciding phrase, in `docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json`, committed
  before any harness or scorer candidate exists.

**Effect:**

1. From the first scored run that carries a `members` key (Phase-41 H-LANE and later), the AXIS
   gate is satisfied when the surviving row's OWN title OR ANY `members[].title` on that row names
   the required mechanism, honoring the row's NOT-clause. SITE and BAND are still judged on the
   surviving row's own `file:line` and `band`.
2. The offline replay guardrail (`plugins/vibe-check/scripts/replay.py`, plan 41-02) applies this
   same basis. It is the manifest's `_rules.axis_basis`.
3. Nothing about `state.passes[-1].findings[]` as the scoring input changes. `filtered[]` is still
   not scored.
4. The rule applies to the Phase-41 spot-check and to Phase 43. The sealed denominators are
   untouched.

**Sign-off:** owner decision D-14, recorded in discuss-phase 2026-09-29 after the Phase-41 research
surfaced the representative-vs-AXIS conflict; registered here before H-LANE lands.

## 008 — 2026-09-29 — v2.9 catch `runs/triggarr-secret-in-logs/run-2` AMENDED in the offline replay guardrail (D-05, Phase 41)

This entry records that ONE recorded catch cannot be reconstructed by the offline replay from its
surviving archive. It supersedes no sealed number and moves no denominator: the sealed verdict below
stands exactly as recorded, and the run stays one of the 26 protected catch runs.

**Sealed statement (verbatim, unchanged):**

From `docs/design/b3-ground-truth/SCORING-b3.md` §3.1 (`triggarr-secret-in-logs`), the run-2 row,
quoted as raw bytes:

```
| 2 | len=1,head=f4366a2 ✓ | ✓ | `codex-adversarial` L232 [critical] "Raw HTTPStatusError logging can leak URL credentials" (compliance L232 [warning] corroborates) | ✓ | ✓ (credential leak) | ✓ (critical) | **catch** | ✓ |
```

From the same file, §5: `**Headline catch-rate = 8/9** (should-catch runs)`.

**Evidence:**

- The v2.9 archive `runs/triggarr-secret-in-logs/run-2/` holds only `state.json`, `tree.diff` and
  `tree.diff.sha256`. `state.passes[-1]` carries `findings[]` with exactly two rows at SITE
  (`triggarr/clients/base.py` L232): `compliance` warning and `codex-adversarial` critical, the
  recorded catch. There is no `filtered[]` and no session transcript, so the scorer's full original
  input set is not archived.
- Replaying those two survivors through the baseline scorer blob (plan 41-02,
  `plugins/vibe-check/scripts/replay.py baseline`) bridges the codex finding into the single
  co-located native domain (`compliance`). Compliance leads the surviving row at critical and the
  codex finding is absorbed into `filtered[]`. The surviving row's title is the one the manifest
  adjudicates axis=false ("names no leaked secret"), and the baseline scorer emits no `members`, so
  the entry-007 member-title rule cannot apply. The replay basis is `axis-false`.
- The most likely cause is native findings at the same site in the original run that made the bridge
  ambiguous and then fell below threshold. They are not in the archive and cannot be recovered. This
  is the reconstruction-fidelity limit for v2.9-era inputs (CONTEXT D-07), not a harness defect.
- Every repair inside the disclosed method was ruled out: a per-run patch, using the archived
  attribution or recorded bands as a scorer input, or inventing the missing inputs.
- The other secret-in-logs catches reproduce under the baseline replay and stay fully protected:
  `runs/triggarr-secret-in-logs/run-1` and `run-3` (v2.9), `runs-v2.10/triggarr-secret-in-logs/run-1..3`
  (Phase 38), and `runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1..3` (Phase 40). The three
  Phase-40 batch spot-check runs were never protected (calibration-only) and are unaffected.

**Effect:**

1. `REPLAY-CATCH-MANIFEST-v2.10.json` gains a `guardrail_amendments` entry for
   `runs/triggarr-secret-in-logs/run-2` that references this entry (`008`). The offline guardrail
   reports that run as AMENDED. It is not excluded and is not counted as REPRODUCED.
2. The baseline replay reads **REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1**. The protected
   denominator stays 26.
3. A candidate scorer is still judged on all 25 REPRODUCED catches. The AMENDED run passes through
   the guardrail unchanged. It neither blocks nor excuses a candidate.
4. Entry 007 is NOT extended. `filtered[]` absorbed members do not count toward AXIS, and
   `filtered[]` is still not scored.
5. The sealed v2.9 verdict (**catch**) and the headline **8/9** stand. The sealed archives are not
   touched. The amendment applies only to the offline replay guardrail, not to how any recorded or
   future live run is scored.

**Sign-off:** owner decision 2026-09-29 (Option 1, "amend"), taken after plan 41-02 stopped at the
D-05 stop rule with this run UNEVALUABLE. Recorded by the assistant.
