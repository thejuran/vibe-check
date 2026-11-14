"""finalize_inputs.py — the Finalize gate inputs, worked out by a tested helper.

WHAT IT TRANSCRIBES. Step 1 ("HEAD fingerprints") of Finalize mode in
`phases/shared/90-finalize.md` (lines 13-22 at 2.14.1, dd8e4ab):

  For every root `fix_verdicts` entry whose `at_pass` equals the last pass's
  `pass_number`, find its finding in the last pass's `findings` by
  `stable_hash` (rows only; absorbed `members[]` are not searched). That
  finding's `file` comes from the reviewed diff and may be attacker-authored,
  so it is validated BEFORE any git call: it must match `PATH_RE`
  (`^[A-Za-z0-9._/-]+$`, imported from fixcommit.py) AND be contained under
  `git rev-parse --show-toplevel` (`guard.contained`). Then three git calls:

      git rev-parse HEAD:<file>
      git diff --quiet HEAD -- <file>
      git diff --cached --quiet -- <file>

  The file is fingerprinted with its HEAD blob only when all three exit 0,
  i.e. when HEAD, the index and the working tree agree on it.

FAIL CLOSED BY OMISSION. A file that fails validation, whose rev-parse fails,
whose working tree or index differs from HEAD, or whose git call could not run
or timed out is left out of the map; the call as a whole is never refused.
Omission is how the map tells `carry_state.py finalize-counts` "unbound", and
that helper fails closed for an absent file. A wrongly shaped state gives `{}`.
With no last-pass fix verdicts no git command runs at all.

WORKING DIRECTORY. The repo root is found from the caller's `cwd` (None =
this process's cwd, the session's working directory); the three per-file
checks then run from that root, so the finding's root-relative file name means
the same file in all three. git reads `HEAD:<file>` from the root whatever the
cwd, but reads the pathspec after `--` relative to the cwd: run from a
subfolder, `sub/c.ts` would mean `sub/sub/c.ts`, match nothing and exit 0, and
a file with unsaved or staged edits would be fingerprinted. The 2.14.1
instructions ran the checks in the session's folder and had that gap; this
helper deliberately does not.

WHAT IT DOES NOT DO. It prints no owner sentence and renders nothing: this
module decides, the prose renders. It does not count or gate.

I/O: stdlib imports exactly {json, os, subprocess, sys}, plus the siblings
`guard` (containment) and `fixcommit` (the PATH_RE constant only; never
validate_paths). Every `subprocess.run` is an argv list with
`timeout=GIT_TIMEOUT` and no shell. git's stderr is captured and discarded,
never returned or printed.
"""

import json  # noqa: F401  (part of the declared import set)
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (the report data, decisions_report)
import carry_state  # noqa: E402  (the counts, finalize_counts)
import finalize_gate  # noqa: E402  (the gate decision)
import guard  # noqa: E402  (the ONE containment source)
from fixcommit import PATH_RE  # noqa: E402  (pre-filter constant only)

GIT_TIMEOUT = 60

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_STATE = 3
EXIT_GATE = 4
EXIT_REPORT = 5

# What the model does next, one value per Finalize branch.
NEXT_ACTIONS = ("write-review-md", "finalize-card", "stop-fallback-cw",
                "stop-fallback-nv", "stop-fallback-medium", "stop-no-state",
                "stop-refused")

# The eight `carry_state.py finalize-counts` keys, in the order
# `phases/shared/90-finalize.md` lists them.
COUNT_KEYS = ("outstanding_cw", "unacknowledged_medium", "undecided_nv",
              "outstanding_cw_hashes", "unacknowledged_medium_hashes",
              "undecided_nv_hashes", "verified_obsolete_hashes",
              "confirmed_fix_awaiting_recheck_hashes")


def _git(args, cwd):
    """Run `git <args>` in `cwd` -> (returncode, stdout text), or None when git
    could not run or timed out. stderr is captured and dropped."""
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.returncode, os.fsdecode(proc.stdout)


def _ok(result):
    return result is not None and result[0] == 0


def _toplevel(cwd):
    """The repo root as git prints it, or "" (which guard.contained refuses)."""
    result = _git(["rev-parse", "--show-toplevel"], cwd)
    if not _ok(result):
        return ""
    return result[1].strip()


def _candidate_files(state):
    """Files named by last-pass fix verdicts, in sorted hash order, de-duplicated."""
    last = state["passes"][-1]
    rows = {}
    for r in last["findings"]:
        if isinstance(r, dict) and isinstance(r.get("stable_hash"), str):
            rows.setdefault(r["stable_hash"], r)
    files = []
    verdicts = state["fix_verdicts"]
    for h in sorted(verdicts):
        v = verdicts[h]
        if not isinstance(v, dict) or v.get("at_pass") != last["pass_number"]:
            continue
        r = rows.get(h)
        if r is None:
            continue
        f = r.get("file")
        if isinstance(f, str) and f not in files:
            files.append(f)
    return files


def _head_blobs(state, cwd):
    files = _candidate_files(state)
    if not files:
        return {}
    root = _toplevel(cwd)
    blobs = {}
    for f in files:
        if not PATH_RE.match(f) or not guard.contained(root, f)[0]:
            continue
        rev = _git(["rev-parse", "HEAD:" + f], root)
        if not _ok(rev):
            continue
        if not _ok(_git(["diff", "--quiet", "HEAD", "--", f], root)):
            continue
        if not _ok(_git(["diff", "--cached", "--quiet", "--", f], root)):
            continue
        blob = rev[1].strip()
        if blob:
            blobs[f] = blob
    return blobs


def head_blobs(state, cwd=None):
    """{file: HEAD blob id} for the last pass's fix verdicts. Never raises;
    {} when there is nothing to fingerprint or the state is wrongly shaped."""
    try:
        return _head_blobs(state, cwd)
    except (KeyError, IndexError, TypeError, AttributeError):
        return {}


# --------------------------------------------------------------------------- #
# The result: counts, gate decision, next action and report bundle.
# --------------------------------------------------------------------------- #
def next_action(action, counts):
    """The next action for a gate `action` and the counts it was decided on.
    Pure; always one of NEXT_ACTIONS."""
    if action == "write":
        return "write-review-md"
    if action in ("outstanding-to-phase-5", "medium-ack-loop"):
        return "finalize-card"
    if action == "fallback":
        if counts["outstanding_cw"] > 0:
            return "stop-fallback-cw"
        if counts["undecided_nv"] > 0:
            return "stop-fallback-nv"
        return "stop-fallback-medium"
    if action == "error":
        return "stop-no-state"
    return "stop-refused"


def _no_state_counts():
    """The counts with no state file: the three counts 0, every list empty."""
    return {k: (0 if i < 3 else []) for i, k in enumerate(COUNT_KEYS)}


def build_result(state, blobs, switches, report_source=None):
    """(exit code, result or None) for a parsed `state` (None = no state file),
    the HEAD fingerprint map `blobs` and the three boolean `switches`.

    The counts come from carry_state.finalize_counts, the decision from
    finalize_gate.run on the seven flags, and on `write` only the report from
    batch_card.decisions_report of the state `report_source()` returns (the
    state given here when no source is passed). Nothing is re-derived here."""
    if state is None:
        counts = _no_state_counts()
    else:
        counts = carry_state.finalize_counts(state, blobs)
        if counts is None:
            return EXIT_STATE, None
    flags = {
        "state_file_present": state is not None,
        "outstanding_cw": int(counts["outstanding_cw"]),
        "unacknowledged_medium": int(counts["unacknowledged_medium"]),
        "undecided_nv": int(counts["undecided_nv"]),
        "noninteractive": bool(switches["noninteractive"]),
        "pr_mode": bool(switches["pr_mode"]),
        "range_mode": bool(switches["range_mode"]),
    }
    try:
        gate = finalize_gate.run({"flags": flags})
        action = gate["action"]
        reason = gate["reason"]
    except Exception:  # noqa: BLE001  (any gate failure is the gate stop)
        return EXIT_GATE, None
    if action not in finalize_gate.ACTIONS:
        return EXIT_GATE, None
    report = None
    if action == "write":
        source = state if report_source is None else report_source()
        if source is not None:
            report = batch_card.decisions_report(source)
        if report is None:
            return EXIT_REPORT, None
    return EXIT_OK, {"action": action, "reason": reason,
                     "next": next_action(action, counts),
                     "counts": {k: counts[k] for k in COUNT_KEYS},
                     "report": report}
