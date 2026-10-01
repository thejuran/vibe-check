"""codex_gate.py — the Codex diff-representability predicate as an executable
decision over bash-gathered facts.

Phase 40 (DIET-02, second tier, D-07). This is a BEHAVIOR-PRESERVING extraction
of `commands/deep-review.md` Phase 2c steps 1-5 (the probe gate at :215, the
diff-targeting rule at :238-251, and the launch guard at :266). The rule is
dense and safety-critical, and it was carried as four pages of prose that a
reader had to re-derive on every run.

THE ONE RULE (deep-review.md:238): run Codex ONLY when its representable review
range can be shown to EXACTLY EQUAL the Phase-0-resolved diff set for the active
mode. Codex can represent exactly two ranges — `--scope working-tree` (the
uncommitted tree) and `--base <ref> --scope branch` (merge-base(HEAD,ref)..HEAD,
COMMITTED ONLY). It cannot represent an arbitrary non-ancestor left boundary, a
right side that is not HEAD, or the UNION of a committed range plus a dirty
tail. If neither representable range provably equals the mode's diff, FAIL
CLOSED.

Why the asymmetry is deliberate (deep-review.md:222): the later Phase-3
`in_diff` clip can drop EXTRA out-of-diff findings, but it cannot recover
defects Codex never reviewed. A wrong SKIP costs a second opinion; a wrong RUN
silently misses real defects while the run looks successful. So every ambiguity
resolves to skip, and that includes malformed input — an unknown mode, a missing
fact, or a fact that is not a bool.

Non-bool facts are refused rather than coerced ON PURPOSE. `1`, `"true"` and
`"false"` are all truthy in Python, so a bash site that emitted `1` instead of
`true` — or, worse, the string `"false"` — would silently decide RUN. Refusing
turns that into a visible skip.

Evaluation order is transcribed from the prose, NOT summarized:

  step 1 (:215)  companion file absent          -> not-installed
  step 2 (:219)  probe NOT-GO                   -> unauthenticated / unavailable
  step 4 (:238)  diff-targeting, `--all` FIRST  -> whole-repo-non-representable
                 then the per-mode arms         -> the range slugs, or RUN
  step 5 (:266)  launch guard                   -> no-timeout-binary
                 then the calibration text      -> focus-unreadable

Note the plan's interface summary placed the `--all` arm BEFORE the probe; the
prose orders it after (step 4 follows step 2, and step 2 is guarded only by
step 1's CODEX_SKIPPED). The prose wins.

The ten reason slugs are SEALED (deep-review.md:355). Each names a distinct
outcome that the Phase-3 status line renders verbatim, so `no-timeout-binary`
("the watchdog is inexpressible, nothing ran") must never be conflated with
`timeout` ("Codex ran and hit the 300s cap"). They live in ONE tuple and every
other reference is an index into it — a hand-typed slug elsewhere is exactly how
ten drift into eleven, and a test asserts no such literal exists.

`focus-unreadable` (Phase 42) is the launch-time precondition that the Codex
calibration text (`templates/codex-focus.txt`) could be read. Codex must never
launch without it, and deciding it here — as a fact, before the disclosure line
and the launch — makes it a labeled skip like every other one instead of a
free-text reason printed from inside the background launch shell.

`timeout` is a member of the sealed set but is never emitted by `decide`: it is
a COLLECTION-time outcome (deep-review.md:314, the 124 exit at Phase 3), not a
dispatch decision. It is carried here so the set stays whole and the Phase-3
renderer has one source for all ten.

Purity (keep-list D-08): no git, filesystem or shell I/O. Every fact — installed,
authenticated, dirty, ancestry — is gathered by the orchestrator's bash and
arrives as data. The `--base` REF is likewise never derived here: `decide` emits
the placeholder token `<base-ref>` and bash substitutes its OWN resolved ref
(deep-review.md:251 — `--base` is never derived from Codex output). Import set
is EXACTLY {json, sys}.

I/O: JSON envelope on stdin -> JSON envelope on stdout. The __main__ shim fails
CLOSED — unparseable stdin propagates so the process exits non-zero.
"""

import json
import sys

# --------------------------------------------------------------------------- #
# The ten sealed reason slugs — deep-review.md:355. NEVER invented, never
# restated as a bare literal anywhere below.
# --------------------------------------------------------------------------- #
SLUGS = (
    "not-installed",
    "unauthenticated",
    "unavailable",
    "whole-repo-non-representable",
    "phase-diff-has-uncommitted-tail",
    "range-not-identical",
    "head-not-at-target",
    "no-timeout-binary",
    "focus-unreadable",
    "timeout",
)

(
    _NOT_INSTALLED,
    _UNAUTHENTICATED,
    _UNAVAILABLE,
    _WHOLE_REPO,
    _UNCOMMITTED_TAIL,
    _RANGE_NOT_IDENTICAL,
    _HEAD_NOT_AT_TARGET,
    _NO_TIMEOUT_BINARY,
    _FOCUS_UNREADABLE,
    _TIMEOUT,  # collection-time only; see the module docstring.
) = SLUGS

# The ref is substituted by bash — deep-review.md:251.
BASE_REF_PLACEHOLDER = "<base-ref>"

_WORKING_TREE_ARGS = ["--scope", "working-tree"]
_BRANCH_ARGS = ["--base", BASE_REF_PLACEHOLDER, "--scope", "branch"]

MODES = ("all", "default", "gsd-empty-range", "gsd-range", "pr", "range")

# All REQUIRED, all bools. A missing or non-bool entry fails closed.
REQUIRED_FACTS = (
    "installed",
    "authenticated",
    "available",
    "timeout_binary",
    "focus_readable",
    "dirty",
    "phase_start_is_ancestor",
    "head_is_upper",
    "a_is_ancestor_of_b",
    "head_is_pr_head",
    "merge_base_matches_pr_base",
)


def _skip(slug):
    return {"action": "skip", "slug": slug, "codex_args": None}


def _run_with(args):
    # A fresh list per call: the caller must not be able to mutate the module
    # constant through the returned decision.
    return {"action": "run", "slug": None, "codex_args": list(args)}


def _facts_valid(facts):
    if not isinstance(facts, dict):
        return False
    for key in REQUIRED_FACTS:
        if not isinstance(facts.get(key), bool):
            return False
    return True


def decide(mode, facts):
    """Decide whether Codex runs. -> {action, slug, codex_args}.

    `action` is "run" or "skip"; on a run `slug` is None and `codex_args` carries
    the companion arguments; on a skip `slug` is one of SLUGS and `codex_args` is
    None. Pure and total: never raises, never reads the environment, and every
    unhandled input skips.
    """
    # Malformed input is a skip, not an exception (fail closed).
    if mode not in MODES or not _facts_valid(facts):
        return _skip(_RANGE_NOT_IDENTICAL)

    # --- step 1 (:215): the companion file is absent. Decided before the probe
    # runs at all — the prose guards step 2 with `[ -z "$CODEX_SKIPPED" ]`.
    if not facts["installed"]:
        return _skip(_NOT_INSTALLED)

    # --- step 2 (:219): probe GO/NOT-GO. `.auth.loggedIn == false` is reported
    # as unauthenticated; a non-zero exit or unparseable JSON as unavailable.
    if not facts["authenticated"]:
        return _skip(_UNAUTHENTICATED)
    if not facts["available"]:
        return _skip(_UNAVAILABLE)

    # --- step 4 (:238): diff-targeting. The `--all` arm is evaluated FIRST in
    # this list (:241) because --all is a branch-flip that wins over every diff
    # detector, so an --all run short-circuits here and never reaches the
    # per-mode arms. A whole-tree selection is NEITHER representable range.
    if mode == "all":
        return _skip(_WHOLE_REPO)

    if mode in ("default", "gsd-empty-range"):
        # The Phase-0 diff IS the uncommitted working tree — the identity case
        # (:246-247). No dirty/committed mismatch is possible, so `dirty` is
        # not consulted.
        args = _WORKING_TREE_ARGS
    elif mode == "gsd-range":
        # :249 — a committed range PLUS a dirty tail is representable as
        # NEITHER the union nor exactly either part. Its own slug, because "the
        # phase has uncommitted edits" is a different operator story from "the
        # range boundaries do not line up".
        if facts["dirty"]:
            return _skip(_UNCOMMITTED_TAIL)
        # :248 — PHASE_START must be an ancestor of HEAD, else Codex's
        # merge-base(HEAD, PHASE_START)..HEAD is not the resolved range.
        if not facts["phase_start_is_ancestor"]:
            return _skip(_RANGE_NOT_IDENTICAL)
        args = _BRANCH_ARGS
    elif mode == "range":
        # :251 — BOTH boundaries, not just the upper ref: (i) HEAD == B, then
        # (ii) A is an ancestor of B.
        if not facts["head_is_upper"]:
            return _skip(_HEAD_NOT_AT_TARGET)
        if not facts["a_is_ancestor_of_b"]:
            return _skip(_RANGE_NOT_IDENTICAL)
        args = _BRANCH_ARGS
    else:  # mode == "pr"
        # :251 — local HEAD must be the PR head SHA, and the local merge-base
        # against the PR base must equal the PR's actual diff base (a stale
        # local base ref is the common cause of the second failure).
        if not facts["head_is_pr_head"]:
            return _skip(_HEAD_NOT_AT_TARGET)
        if not facts["merge_base_matches_pr_base"]:
            return _skip(_RANGE_NOT_IDENTICAL)
        args = _BRANCH_ARGS

    # --- step 5 (:266): the launch guard. Reached only on a RUN mode. Without
    # timeout/gtimeout the self-contained watchdog is inexpressible, so running
    # Codex would mean running it UNBOUNDED (SAFE-02). Skip with its OWN slug —
    # never the `timeout` slug, which means Codex ran and hit the 300s cap.
    if not facts["timeout_binary"]:
        return _skip(_NO_TIMEOUT_BINARY)

    # The calibration text is a launch precondition too: Codex never runs
    # without it. Decided here so the skip is labeled and precedes the
    # disclosure line and the launch; the launch shell keeps an empty-read
    # guard only as a backstop.
    if not facts["focus_readable"]:
        return _skip(_FOCUS_UNREADABLE)

    return _run_with(args)


def run(envelope):
    """{"mode": "<mode>", "facts": {...}} -> the decision. Fails closed."""
    if not isinstance(envelope, dict):
        return _skip(_RANGE_NOT_IDENTICAL)
    return decide(envelope.get("mode"), envelope.get("facts"))


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO. A gate that cannot read its
    # own input must not print a decision.
    json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
