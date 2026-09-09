"""statepath.py — the ONE `.turingmind/state/` filename rule, for every mode.

Phase 40 (DIET-02, second tier, D-07). A BEHAVIOR-PRESERVING extraction of the
per-mode state-path derivations in `commands/review.md` Phase 0.5 (`:405-428`),
governed by the HARD CONTRACT at `:12`.

WHY THIS IS ONE MODULE AND NOT FIVE PROSE RESTATEMENTS. The rule appears at
`review.md:12` (the contract), `:30` (Finalize), `:406`/`:409`/`:418` (Phase
0.5), and `:1096` (the Phase-5 pause message). `:405` requires that the resolved
path bind to ONE canonical `$STATE_FILE` "so every downstream consumer (Phase
4.5 persist, Finalize read/archive) reads the SAME handle regardless of mode —
Finalize must NOT re-derive a path". Five restatements of one rule is exactly
the drift surface this extraction closes.

THE DERIVATIONS, transcribed:

  gsd (review.md:406)
      `.turingmind/state/<$PHASE_ID>.json`, where `$PHASE_ID` is the FULL
      resolved directory name (`02-real-data-path`, NOT `02`). The HARD
      CONTRACT at review.md:12 states the governing rule: `<$PHASE_ID>` is the
      full resolved phase directory name — **never abbreviate**.

  default / pr / range (review.md:409)
      `.turingmind/state/<repo>-<branch-slug>.json`, where `<branch-slug>` is
      the current branch "with every `/` replaced by `-`". The slug step is
      MANDATORY: a raw branch name produces a SLASHED path, which breaks the
      flat-vs-`by-mode/` disjointness guarantee, ENOENTs on write (Phase 0.7
      creates only `.turingmind/state/` itself), and diverges from the
      dash-named files actually on disk.

  all (review.md:418-425)
      `.turingmind/state/by-mode/all/<scope-hash>.json`, where `<scope-hash>` is
      ALWAYS a 12-hex digest — `printf '%s' "<repo>:<branch>:<scope-token>" |
      shasum | cut -c1-12` (review.md:423). The scope token is `$NARROW`, or
      the literal `whole-tree` ONLY when `$NARROW` is empty (review.md:422).
      Note review.md:414:
      the `--all` branch needs NO slug, because `$BRANCH` feeds `shasum` and a
      12-hex digest never carries a slash — so the branch is hashed RAW here.
      Slugging it first would produce a different key than the recorded bash.

`shasum` with no algorithm flag is SHA-1, which is why `hashlib` is in the
import set. The plan specified {json, re, sys}; fix-list FL-05 then required
reproducing the real `--all` key, which is not computable without a real SHA-1.
The addition is deliberate and documented, not drift. `os` is still forbidden
and a test asserts it: this module computes a path, it does NOT check, create,
read or write one.

NAMESPACE DISJOINTNESS (review.md:428) is a structural property, restated here
as a guard: the default branches build a FLAT filename and the `--all` branch
builds a `by-mode/all/` path, so "a plain `/review` can NEVER resolve INTO the
`by-mode/all/` subtree (and `--all` can never resolve out of it)".

FAIL CLOSED, because resolving to the wrong state file silently merges two
reviews' state, or orphans one. An unknown mode, a missing component, an
abbreviated phase id, or a component unsafe as a filename returns
`(None, <fixed reason>)`.

T-40-41: a phase id can originate from a directory name in the REVIEWED repo
and becomes a path component, so `..`, separators, NUL, control characters and
a leading dash are refused. Reasons are drawn from the module-level REASONS
tuple and NEVER echo the offending value.

I/O: stdlib only, imports exactly {hashlib, json, re, sys}. CLI:

    echo '{"mode":"default","repo":"r","branch":"main"}' | python3 statepath.py

JSON stdin -> JSON stdout. Unparseable stdin propagates so the process exits
NON-ZERO.
"""

import hashlib
import json
import re
import sys

# review.md:12 — the HARD CONTRACT's output root.
STATE_DIR = ".turingmind/state"

# review.md:418 — the RESERVED subdirectory for mode-scoped state.
ALL_SUBDIR = "by-mode/all"

# review.md:422 — the literal token used ONLY when $NARROW is empty.
WHOLE_TREE_TOKEN = "whole-tree"

# The mode set, transcribed from Phase 0.5: the GSD branch (:406), the three
# "Other modes (no args / PR / range)" that share one derivation (:409), and
# the `--all` branch (:416).
MODES = ("gsd", "default", "pr", "range", "all")

REASON_OK = "resolved"
REASON_UNKNOWN_MODE = "unknown mode"
REASON_MISSING_COMPONENT = "a required path component is missing"
REASON_ABBREVIATED = "phase id is abbreviated; the full directory name is required"
REASON_UNSAFE_COMPONENT = "a path component is unsafe as a filename"

REASONS = (
    REASON_OK,
    REASON_UNKNOWN_MODE,
    REASON_MISSING_COMPONENT,
    REASON_ABBREVIATED,
    REASON_UNSAFE_COMPONENT,
)

# The "not abbreviated" shape. review.md does not state a regex, so this is the
# WEAKEST rule that still enforces what :406-:408 require: a full phase
# directory name is a numeric-ish prefix, a separator, and at least one more
# segment — which is exactly what distinguishes `02-real-data-path` (✓ Correct,
# :407) from `02` and `31` (🚫 Wrong, :408). Recorded as a documented decision
# rather than presented as transcribed.
PHASE_ID_SHAPE = re.compile(r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)+$")

# Characters that make a component unsafe as a FILENAME (T-40-41).
_UNSAFE_SUBSTRINGS = ("/", "\\", "..", "\x00")


def _is_str(value):
    return isinstance(value, str)


def _safe_component(value):
    """A component that can be interpolated into a filename without escaping.

    Empty is allowed here — an empty BRANCH is a real, recorded value (a
    detached checkout yields `<repo>-.json`; see RUN-CHECKLIST-v2.10.md:297) —
    so emptiness is checked by the caller where it actually matters.
    """
    if not _is_str(value):
        return False
    for bad in _UNSAFE_SUBSTRINGS:
        if bad in value:
            return False
    if value.startswith("-"):
        return False
    if value in (".", ".."):
        return False
    # Control characters (incl. newline/tab) have no place in a filename.
    return not any(ord(ch) < 32 or ord(ch) == 127 for ch in value)


def _refuse(reason):
    return (None, reason)


def _resolve_gsd(phase_id):
    """review.md:406 — the FULL resolved phase directory name, never a prefix."""
    if not _is_str(phase_id) or phase_id == "":
        return _refuse(REASON_MISSING_COMPONENT)
    if not _safe_component(phase_id):
        return _refuse(REASON_UNSAFE_COMPONENT)
    # :408 — `02.json` / `31.json` are the WRONG forms. A bare prefix (or any
    # value failing the full-name shape) is REFUSED, not silently accepted:
    # abbreviating means the next invocation cannot find the state it wrote and
    # carry-forward silently restarts from pass 1 (:406).
    if not PHASE_ID_SHAPE.match(phase_id):
        return _refuse(REASON_ABBREVIATED)
    return ("%s/%s.json" % (STATE_DIR, phase_id), REASON_OK)


def _resolve_flat(repo, branch):
    """review.md:409 — `<repo>-<branch-slug>.json`, a FLAT filename."""
    if not _is_str(repo) or repo == "" or not _is_str(branch):
        return _refuse(REASON_MISSING_COMPONENT)
    if not _safe_component(repo):
        return _refuse(REASON_UNSAFE_COMPONENT)
    # :411 — `git branch --show-current | tr '/' '-'`. Slug FIRST, then check:
    # a slash is legal in a branch name and is what the slug exists to remove.
    slug = branch.replace("/", "-")
    if not _safe_component(slug):
        return _refuse(REASON_UNSAFE_COMPONENT)
    return ("%s/%s-%s.json" % (STATE_DIR, repo, slug), REASON_OK)


def _resolve_all(repo, branch, narrow):
    """review.md:418-425 — `by-mode/all/<12hex>.json`."""
    if not _is_str(repo) or repo == "" or not _is_str(branch):
        return _refuse(REASON_MISSING_COMPONENT)
    if narrow is None:
        narrow = ""
    if not _is_str(narrow):
        return _refuse(REASON_MISSING_COMPONENT)
    # :422 — the literal token 'whole-tree' ONLY when $NARROW is empty.
    scope_token = narrow if narrow else WHOLE_TREE_TOKEN
    # :423 — `printf '%s' "REPO:BRANCH:SCOPE_TOKEN" | shasum | cut -c1-12`.
    # `shasum` with no flag is SHA-1. The branch is hashed RAW, NOT slugged
    # (:414): the digest never carries a slash, and slugging first would
    # produce a different key than the recorded bash.
    payload = "%s:%s:%s" % (repo, branch, scope_token)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return ("%s/%s/%s.json" % (STATE_DIR, ALL_SUBDIR, digest), REASON_OK)


def resolve(mode, phase_id=None, repo=None, branch=None, narrow=None):
    """The ONE state-filename rule. Returns `(path, reason)`; fails closed.

    The signature carries everything the derivations actually need — FL-05
    (finding R9) established that `(mode, phase_id, scope_label)` cannot
    reproduce a single existing key, because the default modes need the repo
    basename and branch slug and `--all` needs a SHA-1 over `repo:branch:scope`.
    This function OWNS that hashing.

    No filesystem access: it computes a path, it does not check or create one.
    """
    if not _is_str(mode) or mode not in MODES:
        return _refuse(REASON_UNKNOWN_MODE)
    if mode == "gsd":
        return _resolve_gsd(phase_id)
    if mode == "all":
        return _resolve_all(repo, branch, narrow)
    # :409 — no args / PR / range share ONE derivation.
    return _resolve_flat(repo, branch)


def run(envelope):
    """{"mode": ..., "repo": ..., "branch": ..., ...} -> {"path", "reason"}."""
    if not isinstance(envelope, dict):
        return {"path": None, "reason": REASON_UNKNOWN_MODE}
    path, reason = resolve(
        envelope.get("mode"),
        phase_id=envelope.get("phase_id"),
        repo=envelope.get("repo"),
        branch=envelope.get("branch"),
        narrow=envelope.get("narrow"),
    )
    return {"path": path, "reason": reason}


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO.
    json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
