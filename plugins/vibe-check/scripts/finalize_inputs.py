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

WORKING DIRECTORY. Every git call runs in the caller's `cwd` (None = this
process's cwd, the session's working directory), exactly where the 2.14.1
instructions ran them. Calls are not re-rooted at the repo root: git reads
`HEAD:<file>` from the root whatever the cwd, and reads the pathspec after
`--` relative to the cwd; re-rooting would make this helper stricter than
2.14.1 for a session that sits in a subdirectory.

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

import guard  # noqa: E402  (the ONE containment source)
from fixcommit import PATH_RE  # noqa: E402  (pre-filter constant only)

GIT_TIMEOUT = 60


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
        rev = _git(["rev-parse", "HEAD:" + f], cwd)
        if not _ok(rev):
            continue
        if not _ok(_git(["diff", "--quiet", "HEAD", "--", f], cwd)):
            continue
        if not _ok(_git(["diff", "--cached", "--quiet", "--", f], cwd)):
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
