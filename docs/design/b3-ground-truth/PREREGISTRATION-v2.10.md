# B3 v2.10 Pre-registration manifest (seal-1, staged two-commit seal)

This manifest pre-registers the v2.10 pass bar and decision rule BEFORE any v2.10 baseline
run and provably BEFORE any Phase-39+ change to `plugins/vibe-check/`. It EXTENDS — and
never touches — the v2.9 seal (`PREREGISTRATION.md`, `ANSWER-KEY-b3.md`, `runs/`, the
existing kit files under `diffs/`): anyone re-deriving the proofs sees two clean,
independent seals.

## The pass bar (sealed at seal-1)

v2.10 FP-rate on the full grown set ≤ ½ × the SET-03 baseline FP-rate, AND catch-rate on
the same diffs no worse than baseline.

Catch and FP are defined identically to v2.9 D-07/D-08: catch = SITE + AXIS + BAND (all
three gates); right-site-wrong-axis or below-band = detected-below-threshold = a MISS in
the headline number. FP = any critical/warning finding on a should-quiet run (medium/low =
noise-notes, not FPs). All rates are exact fractions, no rounding (D-09).

## The decision rule (sealed at seal-1, evaluated in Phase 43, not this phase)

At most ONE retune, on failed diffs only (×3); whether it was used or not is recorded.

## The denominator rule (rates now, literal numbers at seal-2)

The pass bar is evaluated as RATES over complete pre-registered denominators: all
committed diffs of the v2.10 set, ×3 each; per-role denominators = diffs-in-role × 3.
The literal numbers are deferred to seal-2, which knows the final set count and records
them as the three bare `DENOM_CATCH_RUNS:` / `DENOM_QUIET_RUNS:` / `DENOM_TOTAL_RUNS:`
lines under the reserved final section (see the staged-seal rule below). No aggregation
over holes: a missing or unscoreable run leaves its denominator slot explicitly open —
it is repeated or disclosed, never silently dropped.

## Carried-over key reference (quoted from the v2.9 manifest, NOT re-derived)

ANSWER_KEY_COMMIT: ef0ab67cb45957167c99eff468077348432e1474
ANSWER_KEY_SHA256: 1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1

Carried-over diffs are scored against THAT blob
(`git show ef0ab67cb45957167c99eff468077348432e1474:docs/design/b3-ground-truth/ANSWER-KEY-b3.md`);
new diffs are scored against the blob seal-2 will register.

## Ordering attestation A (the SET-02 proof)

At this commit, `git diff v2.9 -- plugins/vibe-check/` is EMPTY — the measured plugin is
byte-identical to shipped 2.9.0. Any later verifier re-derives this: the first commit
after SEAL1_COMMIT touching `plugins/vibe-check/` must postdate it, so the bar provably
precedes every COMPAT/DIET/SCORER/AGENT change.

## Ordering attestation B

No `docs/design/b3-ground-truth/runs-v2.10` path exists at this commit
(`test ! -e docs/design/b3-ground-truth/runs-v2.10` succeeds) — the bar provably precedes
every v2.10 run artifact.

## The staged-seal rule (two-commit budget + ordered append-only whitelist)

This manifest receives EXACTLY ONE follow-up commit (seal-2), and that commit is a PURE
BYTE-APPEND: it adds, at EOF under the reserved `## Seal-2 (append-only)` section, ONLY
the five whitelisted lines IN THIS EXACT ORDER, each newline-terminated —
`NEW_ANSWER_KEY_COMMIT: <40-hex>`, `NEW_ANSWER_KEY_SHA256: <64-hex>`,
`DENOM_CATCH_RUNS: <int>`, `DENOM_QUIET_RUNS: <int>`, `DENOM_TOTAL_RUNS: <int>` —
nothing else, and no other edit ever. Every seal-1 byte (pass bar, decision rule,
attestations, this rule) must survive seal-2 unmodified. Seal-2 must strictly precede
the first `runs-v2.10/<new-diff-id>/` commit.

Verifier derivation: SEAL1 = the first commit touching this file; SEAL2 = the only other.
HARD-FAIL if more than 2 commits touch this file, if any manifest commit also contains
`runs-v2.10/` content, OR if the raw BYTES of `git show SEAL2:<this file>` do not equal
the raw BYTES of `git show SEAL1:<this file>` followed by exactly the five whitelisted
lines in order (byte prefix equality — startswith semantics, zero modified or deleted
seal-1 bytes; a seal-2 that rewrites the already-used pass bar, or rewrites LF line
endings to CRLF, fails this check even at commit count 2). The canonical executable form
of this check is `docs/design/b3-ground-truth/verify-seal2-append.py` (committed and
self-tested by plan 38-02); every later gate — the 38-04 seal step, both checklist gates
when 2 manifest commits exist, the 38-05 scoring ladder, and the 38-06 phase exit —
INVOKES that committed file rather than re-deriving or hand-transcribing the check.

Old-6 run commits landing BETWEEN seal-1 and seal-2 are LEGAL — their key sealed at the
v2.9 manifest on 2026-07-03.

## Fail-closed scoring invariant (v2.10 form — both key blobs, `runs-v2.10/` pathspec)

The v2.10 scoring (38-05) MUST:

1. Recompute
   `git show ef0ab67cb45957167c99eff468077348432e1474:docs/design/b3-ground-truth/ANSWER-KEY-b3.md | shasum -a 256`
   and EXIT NON-ZERO if it differs from the carried `ANSWER_KEY_SHA256` value quoted
   above, AND recompute
   `git show <NEW_ANSWER_KEY_COMMIT>:docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md | shasum -a 256`
   and EXIT NON-ZERO if it differs from the seal-2 `NEW_ANSWER_KEY_SHA256` value — it
   REFUSES to score on either mismatch.
2. Parse the SCORED key rows FROM those committed blobs — carried-over rows from the v2.9
   blob at the carried `ANSWER_KEY_COMMIT`, new rows from the blob at the seal-2
   `NEW_ANSWER_KEY_COMMIT` — never from a live working file; an edited live key is inert.
3. Require `git merge-base --is-ancestor` to exit 0 for BOTH key commits against HEAD,
   AND every commit touching `docs/design/b3-ground-truth/runs-v2.10/` to descend from
   SEAL1 (new-diff run commits additionally from SEAL2) — proving the keys that scored
   the runs are byte-identical to the pre-registered ones and the bar strictly precedes
   every v2.10 run artifact.

The verifier reads the sealed proof values from
`git show MANIFEST_COMMIT:docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md` (seal-1
values from SEAL1, seal-2 values from SEAL2), never the live file. No output-dependent
edit to either key — or to this manifest — can survive that gate.

## Seal-2 (append-only)

The single follow-up commit appends exactly five bare lines — `NEW_ANSWER_KEY_COMMIT`,
`NEW_ANSWER_KEY_SHA256`, `DENOM_CATCH_RUNS`, `DENOM_QUIET_RUNS`, `DENOM_TOTAL_RUNS` — in
the declared order, beneath this header; field names in this sentence are backticked so
no whitelist-shaped line exists before seal-2.
NEW_ANSWER_KEY_COMMIT: 5f687d95f9be4fef2c0fcd78491c308d4c3861e8
NEW_ANSWER_KEY_SHA256: f58f888c9f4dc86d0e34d5a152c781cb7e9913087405e6e25980bd77e3d753d4
DENOM_CATCH_RUNS: 15
DENOM_QUIET_RUNS: 21
DENOM_TOTAL_RUNS: 36
