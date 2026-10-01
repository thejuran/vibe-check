"""coverage_gate.py — diff-mode dispatch gate for test-sufficiency (GATE-01).

Turns the two path lists gathered while building the diff-mode
`<coverage-artifacts>` block into a sealed `{dispatch, case}` verdict, so the
fact "the coverage block is empty" reaches dispatch, selection, and the report
as printed, transcript-visible evidence instead of a remembered prose rule.

THE ONE RULE (`phases/deep-review/01d-coverage.md`, EMPTY CASE (D-02), and the
USABLE ARTIFACT GATE arms (b)/(c)/(d)):

    The test-sufficiency lane is dispatched exactly when the injected
    coverage block is non-empty.

  - Nothing discovered (found is empty): do not dispatch; case no-artifact.
  - Something discovered, but nothing survived the usable-artifact gate
    (including a lone binary `.coverage`, which is discovered but never read
    as text): do not dispatch; case none-usable.
  - At least one artifact injected: dispatch exactly as today; case present.

Scope: diff mode only. The `--all` per-chunk assembly (STAGE B) and
`phases/review/20-dispatch-all.md` never call this helper; they keep their
existing empty-block skip-and-note behavior.

WHAT THIS MODULE DOES NOT DO (keep-list). This module decides; the prose
renders. No function returns a rendered string or a report line. No input path
is ever echoed: the output keys are exactly `dispatch` and `case`, and the case
values come only from the sealed CASES tuple. It reads no file, globs nothing,
and has no `--all` logic.

MALFORMED INPUT. Unlike the other gate helpers, which return a fail-closed
decision object, this helper prints NOTHING on stdout and exits 2 when the
input parses as JSON but is malformed: wrong key set, a value that is not a
list, an element that is not a non-empty string, or an injected path that is
not among the found paths. The safe direction here is "dispatch the lane as
today", and a verdict that might be wrong must not be printed where the
orchestrator could act on it. A fixed `refused:` reason goes to stderr.

I/O: stdlib only, imports exactly {json, sys}. CLI:

    echo '{"found":["coverage.xml"],"injected":[]}' | python3 coverage_gate.py

prints dispatch false with case none-usable as a JSON object. Unparseable
stdin propagates so the process exits NON-ZERO: a helper that cannot read its
own input must not print an answer.
"""

import json
import sys

# Sealed. The prose consumers (the gating paragraph in
# `phases/deep-review/20-selection.md` and the Test Coverage render in
# `commands/deep-review.md`) branch on exactly these three values. Never invent
# a fourth; every other reference in this module is a name unpacked below.
CASES = ("present", "no-artifact", "none-usable")

(_PRESENT, _NO_ARTIFACT, _NONE_USABLE) = CASES

# The exact envelope key set. An extra key is refused, not ignored: an
# envelope carrying a field this helper does not understand was built by a
# caller that does not match this contract.
KEYS = ("found", "injected")

_REFUSED = "refused: malformed coverage-gate input\n"


def _is_path(value):
    """A path is a plain non-empty str.

    Types are checked strictly: `bool`, numbers, `None`, and nested containers
    are refused rather than coerced, so a bash site that emitted the wrong
    shape can never be read as a real file name.
    """
    return isinstance(value, str) and value != ""


def _is_path_list(value):
    """A list (never judged by truthiness) whose every element is a path."""
    return isinstance(value, list) and all(_is_path(v) for v in value)


def decide(found, injected):
    """Map validated path lists to a fresh `{dispatch, case}` dict.

    Assumes `run()` already validated the input.
    """
    if injected:
        return {"dispatch": True, "case": _PRESENT}
    if not found:
        return {"dispatch": False, "case": _NO_ARTIFACT}
    return {"dispatch": False, "case": _NONE_USABLE}


def run(envelope):
    """Validate the envelope; return the decision, or None when malformed."""
    if not isinstance(envelope, dict) or set(envelope) != set(KEYS):
        return None
    found = envelope["found"]
    injected = envelope["injected"]
    if not (_is_path_list(found) and _is_path_list(injected)):
        return None
    # An injected path that was never discovered means the caller invented a
    # block. Refuse, so the lane is dispatched as today.
    if not set(injected) <= set(found):
        return None
    return decide(found, injected)


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO.
    result = run(json.load(sys.stdin))
    if result is None:
        sys.stderr.write(_REFUSED)
        sys.exit(2)
    json.dump(result, sys.stdout, allow_nan=False)
