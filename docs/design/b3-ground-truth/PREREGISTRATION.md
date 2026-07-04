# B3 Pre-registration manifest (SEPARATE, fail-closed)

This manifest proves the B3 answer key was frozen BEFORE any run — written in a FOLLOW-UP
commit after the key's freezing commit, so the key blob never contains its own hash (codex
pass-3 fix 1: a blob cannot contain its own digest; the seal must be external).

## The pre-registered proof

ANSWER_KEY_COMMIT: ef0ab67cb45957167c99eff468077348432e1474
ANSWER_KEY_SHA256: 1463544803309db052c0d33e19af1022d4d424b81c5e8b42f9c6d29c34b3fca1

## Convention

ANSWER_KEY_COMMIT is the commit whose tree holds the final `ANSWER-KEY-b3.md`;
ANSWER_KEY_SHA256 is `shasum -a 256` of
`git show ANSWER_KEY_COMMIT:docs/design/b3-ground-truth/ANSWER-KEY-b3.md`
(the digest of the COMMITTED blob, not the working file — re-derivable by anyone from git
history alone).

## The Wave-3 fail-closed invariant

Wave 3 (36-03 scoring) MUST:

1. Recompute `git show ANSWER_KEY_COMMIT:docs/design/b3-ground-truth/ANSWER-KEY-b3.md |
   shasum -a 256` and EXIT NON-ZERO if it differs from ANSWER_KEY_SHA256 above — it REFUSES
   to score on mismatch.
2. Parse the SCORED key rows FROM that committed blob, never from the live working file — an
   edited live key is inert.
3. Require `git merge-base --is-ancestor ANSWER_KEY_COMMIT HEAD` to exit 0 AND every commit
   touching `docs/design/b3-ground-truth/runs/` to descend from ANSWER_KEY_COMMIT — proving
   the key that scored the runs is byte-identical to the pre-registered one and strictly
   precedes every run artifact.

## Immutability rule (codex pass-4 fix 1)

**This file must NEVER be modified once the first `runs/` commit exists.** Wave 3 derives
MANIFEST_COMMIT — the last commit touching this file that STRICTLY PRECEDES the first
`runs/` commit — EXITS NON-ZERO on any later manifest commit or on a commit landing this
file together with `runs/`, and reads the scored proof from
`git show MANIFEST_COMMIT:docs/design/b3-ground-truth/PREREGISTRATION.md`, never the live
file. No output-dependent edit to the key — or to this manifest — can survive that gate.

## Ordering attestation (at manifest-write time)

No `docs/design/b3-ground-truth/runs/` directory existed when this manifest was committed:
the key and this manifest strictly precede every run artifact in git history
(pre-registration ordering).
