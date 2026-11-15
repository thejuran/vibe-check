"""finalize_inputs.py — the Finalize gate inputs, worked out by a tested helper.

USAGE.

    python3 finalize_inputs.py --state-file PATH --blob-out PATH \
        --noninteractive true|false --pr-mode true|false --range-mode true|false

All five arguments are required; a switch is exactly `true` or `false`.
`--blob-out` must be an existing EMPTY regular file (a fresh mktemp per
attempt): the fingerprint map is always rebuilt from the current HEAD, index
and working tree and written there, never read back from an earlier attempt.

stdout (exit 0), one JSON object:
    {"action": <gate action>, "reason": <gate reason>, "next": <NEXT_ACTIONS>,
     "counts": {the 8 finalize-counts keys}, "report": {"entries": [...]} | null}

    exit 0  result printed
         2  usage error, or a bad --blob-out
         3  state file unreadable or malformed
         4  gate stage or internal failure
         5  report failed on `write`

stderr: on a counting-stage refusal (state not JSON or malformed; bad
--blob-out) exactly the one line `carry_state.py finalize-counts` prints at
2.14.1 for that input; on a report-stage refusal (exit 5) exactly the line
`batch_card.py decisions-report` prints for the state file it reads again;
on every other exit nothing. The helper prints no owner sentence: the
instructions map each exit code to the existing sentence. It never echoes a
path, hash or title. It writes only `--blob-out`; the state file is never
written.

The counts come from `carry_state.finalize_counts`, the decision from
`finalize_gate.run` on the seven flags, and on `write` the report bundle from
`batch_card.decisions_report`; no counting or branching rule is re-derived
here. A missing state file (`[ -f "$STATE_FILE" ]` false, including an empty
path) gives the gate's `error` result without reading `--blob-out` or running
git, as at 2.14.1.

WHAT IT TRANSCRIBES. Step 1 ("HEAD fingerprints") of Finalize mode in
`phases/shared/90-finalize.md` (lines 13-22 at 2.14.1, dd8e4ab):

  For every root `fix_verdicts` entry whose `at_pass` equals the last pass's
  `pass_number`, find its finding in the last pass's `findings` by
  `stable_hash` (rows only; absorbed `members[]` are not searched). That
  finding's `file` comes from the reviewed diff and may be attacker-authored,
  so it is validated BEFORE any git call: it must match `PATH_RE`
  (`^[A-Za-z0-9._/-]+$`, imported from fixcommit.py) AND pass the guard
  command `guard.py --root <git rev-parse --show-toplevel> --path <file>`
  with exit 0 (`guard.main`, run in-process with its output dropped). The
  command's argument parsing is part of the check: a name argparse reads as
  an option (most names starting with `-`) exits 2 and is left out, as at
  2.14.1. Then three git calls:

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
module decides, the prose renders.

I/O: stdlib imports exactly {io, json, os, subprocess, sys}, plus the
siblings `batch_card`, `carry_state` and `finalize_gate` (called in-process),
`guard` (the containment command, `main`) and `fixcommit` (the PATH_RE constant only; never
validate_paths). Every `subprocess.run` is an argv list with
`timeout=GIT_TIMEOUT` and no shell. git's stderr is captured and discarded,
never returned or printed.
"""

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (the report data, decisions_report)
import carry_state  # noqa: E402  (the counts, finalize_counts)
import finalize_gate  # noqa: E402  (the gate decision)
import guard  # noqa: E402  (the ONE containment source, as a command)
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


def _guard_command_accepts(root, f):
    """Would `python3 guard.py --root <root> --path <f>` exit 0?

    2.14.1 ran the containment check as that command, so argparse first
    reads `<f>`: a value that looks like an option (most names starting
    with `-`, by this interpreter's rules) makes it exit 2 and the file is
    left out. This runs the same `guard.main` in-process, its stdout and
    stderr captured and dropped, so the rule cannot drift from the
    command's."""
    saved = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = io.StringIO()
    try:
        return guard.main(["--root", root, "--path", f]) == 0
    finally:
        sys.stdout, sys.stderr = saved


def _head_blobs(state, cwd):
    files = _candidate_files(state)
    if not files:
        return {}
    root = _toplevel(cwd)
    blobs = {}
    for f in files:
        if not PATH_RE.match(f) or not _guard_command_accepts(root, f):
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


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
ARGV_FLAGS = ("--state-file", "--blob-out", "--noninteractive", "--pr-mode",
              "--range-mode")
_SWITCH_FLAGS = (("--noninteractive", "noninteractive"),
                 ("--pr-mode", "pr_mode"), ("--range-mode", "range_mode"))
_BOOL_VALUES = {"true": True, "false": False}


def parse_argv(argv):
    """(state file, blob-out, switches) or None on any usage error. Every flag
    is required and has no default; an unknown, repeated or valueless flag is
    an error; a switch is exactly `true` or `false`. The state file may be
    an empty string (read as no state file, as `[ -f "" ]` is)."""
    values = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token not in ARGV_FLAGS or token in values or i + 1 >= len(argv):
            return None
        values[token] = argv[i + 1]
        i += 2
    if set(values) != set(ARGV_FLAGS):
        return None
    switches = {}
    for flag, name in _SWITCH_FLAGS:
        if values[flag] not in _BOOL_VALUES:
            return None
        switches[name] = _BOOL_VALUES[values[flag]]
    return values["--state-file"], values["--blob-out"], switches


def _read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _load_state(path):
    """(state, None), or (None, the refusal line) where the line is the one the
    2.14.1 command prints for this file, or "" when none is shown."""
    try:
        text = _read_text(path)
    except UnicodeDecodeError:
        return None, carry_state.REASON_STATE_JSON
    except OSError:
        return None, ""
    try:
        state = carry_state.load_json_text(text)
    except ValueError:
        return None, carry_state.REASON_STATE_JSON
    reason = carry_state.state_reason(state)
    if reason is not None:
        return None, reason
    return state, None


def _blob_out_ok(path):
    """True only for an existing, empty regular file."""
    try:
        return os.path.isfile(path) and os.path.getsize(path) == 0
    except OSError:
        return False


def _refuse(code, line):
    if line:
        sys.stderr.write(line)
    return code, ""


def _run(state_file, blob_out, switches, cwd):
    if not os.path.isfile(state_file):
        code, result = build_result(None, {}, switches)
        if code != EXIT_OK:
            return code, ""
        return code, json.dumps(result, allow_nan=False)
    state, line = _load_state(state_file)
    if state is None:
        return _refuse(EXIT_STATE, line)
    if not _blob_out_ok(blob_out):
        return _refuse(EXIT_USAGE, carry_state.REASON_HEAD_BLOBS)
    blobs = head_blobs(state, cwd)
    try:
        with open(blob_out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(blobs, sort_keys=True))
    except OSError:
        return _refuse(EXIT_USAGE, carry_state.REASON_HEAD_BLOBS)
    report_line = []

    def reread():
        again, again_line = _load_state(state_file)
        if again is None:
            report_line.append(again_line)
        return again

    code, result = build_result(state, blobs, switches, report_source=reread)
    if code == EXIT_REPORT:
        return _refuse(code, report_line[0] if report_line else "")
    if code != EXIT_OK:
        return code, ""
    return code, json.dumps(result, allow_nan=False)


def run(argv, cwd=None):
    """CLI body. Returns (exit code, stdout text). git runs in `cwd` (None =
    this process's working directory)."""
    parsed = parse_argv(argv)
    if parsed is None:
        return EXIT_USAGE, ""
    state_file, blob_out, switches = parsed
    try:
        return _run(state_file, blob_out, switches, cwd)
    except Exception:  # noqa: BLE001  (the exit code is the diagnostic)
        return EXIT_GATE, ""


# --------------------------------------------------------------------------- #
# Process shim: the only stdout write and the exit.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    _code, _out = run(sys.argv[1:])
    if _out:
        sys.stdout.write(_out)
    sys.exit(_code)
