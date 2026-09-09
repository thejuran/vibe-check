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
