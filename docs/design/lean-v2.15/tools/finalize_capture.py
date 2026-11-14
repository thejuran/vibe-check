"""Offline capture of the five Finalize comparison situations at a pinned commit.

"Same behaviour" for Finalize means that five named situations, walked
offline, produce the same normalised record byte for byte. This module holds
what that comparison needs and keeps the parts apart:

* the situation definitions (`SITUATIONS`): each situation's inputs (which
  fixture, how the state is prepared, the owner's answers) and the one output
  schema every situation fills (`OUTPUT_KEYS`), with no reference to how the
  steps are run, so a later driver that calls helpers instead of walking
  fences can produce the same outputs for the same inputs;
* the pinned tree, normalisation and fingerprints;
* the drivers, one per plugin version, which walk a situation and return the
  outputs dict.

Pinning. The plugin is read from one exact commit (`BASELINE_COMMIT`, the
release tagged v2.14.1), never from the working tree: `materialize` runs
`git archive` of that commit's `plugins/vibe-check` into a temp directory, and
that copy is the `VC_ROOT` every step runs against, the source of the
instruction text and the source of the fixtures. The record therefore keeps
re-deriving the same way after the working tree changes.

Isolation. Nothing from the pinned tree is imported into this process. Every
helper call and every state preparation runs in a child process
(`python3 <pinned scripts>/<helper>.py ...`, or `python3 -I -c` with the
pinned scripts directory put on that child's `sys.path`). The plugin's own
tests import the working-tree copies of the same module names in the same
test process, so an in-process import could silently mix the two.

What is fingerprinted, per situation: each step's exit code and normalised
standard output; the gate decisions in order; the one stop sentence shown to
the owner, or none; the `batch_card.py decisions-report` JSON (the
deterministic report text; the REVIEW.md prose itself is written by the
model); the names of the files written and archived, relative to the
situation's work directory; whether the state file ended up closed; and a
step tally. Standard error is recorded only as present or absent: its text
comes partly from system tools that word errors differently on macOS and
Linux and is not plugin behaviour.

Fences. A fence is every ```bash block in the instruction file, indented
blocks and the one four-backtick block included: the same definition the
plugin's own fence tests and the step-counting rule use. At v2.14.1
`phases/shared/90-finalize.md` holds 18 of them; the ones that print
`BLOBFILE=` and `GATEFILE=` are indented, so a reader that only looks at
column 0 finds 9 and loses them.

Normalisation (`NORMALISATION`, written into every record): machine-specific
paths and times are replaced by fixed tokens before anything is
fingerprinted.

CLI:
  python3 docs/design/lean-v2.15/tools/finalize_capture.py capture --repo <root> --out <json>
  python3 docs/design/lean-v2.15/tools/finalize_capture.py verify --repo <root> --record <json>
`capture` walks the situations at the pinned commit (or `--commit`) and writes
the record; `verify` re-captures and compares against a committed record.
Exit codes: 0 ok; 1 the re-capture differs from the record; 2 unusable input
(unknown commit, unknown or not-yet-walkable situation, unreadable record).
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

BASELINE_COMMIT = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"  # tag v2.14.1
SCHEMA = 1
PLUGIN_REL = "plugins/vibe-check"
FINALIZE_REL = "phases/shared/90-finalize.md"
GIT_TIMEOUT = 60
FENCE_TIMEOUT = 60

WORK_TOKEN = "<WORK>"
VC_ROOT_TOKEN = "<VC_ROOT>"
TIME_TOKEN = "<TIME>"

NORMALISATION = (
    "The situation's work directory path (as given and as resolved) becomes "
    "<WORK>.",
    "The pinned plugin tree's path (as given and as resolved) becomes "
    "<VC_ROOT>.",
    "A mktemp suffix after `vc.` (six letters or digits) becomes vc.XXXXXX.",
    "An ISO date or date-time (YYYY-MM-DD, optionally with a time and zone) "
    "becomes <TIME>.",
    "A ten-digit epoch stamp starting with 1 (optionally with a fraction) "
    "becomes <TIME>.",
    "Standard error is recorded only as present or absent, never as text.",
)

# One output schema for all five situations, fixed before any driver exists.
OUTPUT_KEYS = ("steps", "gate", "stop_sentence", "report", "files_written",
               "files_archived", "state_closed", "tally")
STEP_KEYS = ("id", "exit", "stdout", "stderr_present")
TALLY_KEYS = ("commands_run", "values_carried", "writes")

SIX_ROW = "scripts/fixtures/iplayarr45-six-row-state.json"
LOOP_STATE = "scripts/fixtures/phase45-loop-state.json"

# The owner's answers are fixed strings: the answers the existing 2.14.1
# card-route walk gives (every shown row dismissed with the reason "walk").
SITUATIONS = {
    "clean-close": {
        "title": "clean close that writes the report",
        "inputs": {
            "fixture": LOOP_STATE,
            "state": ("the fixture with every open finding dismissed through "
                      "the pinned carry_state record_decisions (reason "
                      "'walk'), so no decision is outstanding"),
            "head_blobs": {},
            "flags": {"noninteractive": False, "pr_mode": False,
                      "range_mode": False},
            "prior_review_md": None,
            "owner_answers": [],
        },
    },
    "card-first": {
        "title": "close with open decisions that shows the card first",
        "inputs": {
            "fixture": SIX_ROW,
            "state": "the fixture as committed (five critical/warning and "
                     "one medium undecided)",
            "head_blobs": {},
            "flags": {"noninteractive": False, "pr_mode": False,
                      "range_mode": False},
            "prior_review_md": None,
            "owner_answers": [{"q1": "dismiss 1,2,3,4,5,6 -- walk",
                               "q2": None}],
        },
    },
    "one-rebuild": {
        "title": "the one automatic rebuild after a missing input",
        "inputs": {
            "fixture": LOOP_STATE,
            "state": ("the clean-close state; the first attempt's gate input "
                      "file is left empty (the Write failed), so the one "
                      "rebuild mints a new BLOBFILE and GATEFILE"),
            "head_blobs": {},
            "flags": {"noninteractive": False, "pr_mode": False,
                      "range_mode": False},
            "prior_review_md": None,
            "owner_answers": [],
        },
    },
    "refused-close": {
        "title": "a refused or failed close that writes nothing and archives "
                 "nothing",
        "inputs": {
            "fixture": LOOP_STATE,
            "state": ("the clean-close state; the gate input is malformed on "
                      "both attempts, so Finalize stops with the one stop "
                      "sentence"),
            "head_blobs": {},
            "flags": {"noninteractive": False, "pr_mode": False,
                      "range_mode": False},
            "prior_review_md": None,
            "owner_answers": [],
        },
    },
    "fresh-shell-restart": {
        "title": "restart in a fresh shell",
        "inputs": {
            "fixture": SIX_ROW,
            "state": ("the fixture as committed; after the card answer is "
                      "recorded, the gate is re-run from a fresh shell on a "
                      "new GATEFILE built from re-counted, re-fingerprinted "
                      "inputs"),
            "head_blobs": {},
            "flags": {"noninteractive": False, "pr_mode": False,
                      "range_mode": False},
            "prior_review_md": None,
            "owner_answers": [{"q1": "dismiss 1,2,3,4,5,6 -- walk",
                               "q2": None}],
        },
    },
}

# The house fence definition (indented fences included; a four-backtick
# opener contains the three-backtick one, so it is found too).
FENCE_RE = re.compile(r"```bash\n(.*?)\n[ \t]*```", re.S)
_MKTEMP_RE = re.compile(r"\bvc\.[A-Za-z0-9]{6}(?![A-Za-z0-9])")
_ISO_TIME_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}"
    r"(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?"
    r"(?![0-9])")
_EPOCH_RE = re.compile(r"(?<![0-9A-Za-z])1\d{9}(?:\.\d+)?(?![0-9A-Za-z])")


class UsageError(Exception):
    """Unusable input: unknown commit, unknown situation, bad record."""


class CaptureError(UsageError):
    """A walk did not reach the situation's documented outcome."""


# --------------------------------------------------------------------------- #
# Pinned tree
# --------------------------------------------------------------------------- #
def materialize(repo, commit, dest):
    """Extract `plugins/vibe-check` at `commit` into `dest`; return the plugin
    root inside it. Raises UsageError when the commit cannot be archived."""
    if not isinstance(commit, str) or not commit or commit.startswith("-"):
        raise UsageError("not a commit id: %r" % (commit,))
    arc = subprocess.run(["git", "-C", repo, "archive", "--format=tar",
                          commit, PLUGIN_REL],
                         capture_output=True, timeout=GIT_TIMEOUT)
    if arc.returncode != 0 or not arc.stdout:
        raise UsageError("cannot archive %s at %s: %s" % (
            PLUGIN_REL, commit, arc.stderr.decode("utf-8", "replace").strip()))
    untar = subprocess.run(["tar", "-x", "-C", dest], input=arc.stdout,
                           capture_output=True, timeout=GIT_TIMEOUT)
    if untar.returncode != 0:
        raise UsageError("cannot unpack the archive of %s: %s" % (
            commit, untar.stderr.decode("utf-8", "replace").strip()))
    root = os.path.join(dest, *PLUGIN_REL.split("/"))
    if not os.path.isfile(os.path.join(root, *FINALIZE_REL.split("/"))):
        raise UsageError("%s at %s holds no %s" % (PLUGIN_REL, commit,
                                                    FINALIZE_REL))
    return root


# --------------------------------------------------------------------------- #
# Normalisation and fingerprints
# --------------------------------------------------------------------------- #
def _path_forms(path):
    if not path:
        return []
    forms = {path.rstrip("/"), os.path.realpath(path).rstrip("/")}
    return sorted((f for f in forms if f), key=len, reverse=True)


def normalise(text, workdir, vc_root=None):
    """`text` with the NORMALISATION rules applied."""
    for form in _path_forms(workdir):
        text = text.replace(form, WORK_TOKEN)
    for form in _path_forms(vc_root):
        text = text.replace(form, VC_ROOT_TOKEN)
    text = _MKTEMP_RE.sub("vc.XXXXXX", text)
    text = _ISO_TIME_RE.sub(TIME_TOKEN, text)
    return _EPOCH_RE.sub(TIME_TOKEN, text)


def normalise_obj(obj, workdir, vc_root=None):
    """`obj` with every string (keys included) normalised."""
    if isinstance(obj, str):
        return normalise(obj, workdir, vc_root)
    if isinstance(obj, list):
        return [normalise_obj(v, workdir, vc_root) for v in obj]
    if isinstance(obj, dict):
        return {normalise(k, workdir, vc_root): normalise_obj(v, workdir,
                                                              vc_root)
                for k, v in obj.items()}
    return obj


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj):
    """Canonical JSON text: sorted keys, compact separators, UTF-8 kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_sha256(obj):
    return sha256_bytes(canonical_json(obj).encode("utf-8"))


# --------------------------------------------------------------------------- #
# Fences
# --------------------------------------------------------------------------- #
def extract_fences(text):
    """The bodies of every ```bash fence, in file order."""
    return FENCE_RE.findall(text)


def fence_holding(fences, needle):
    """The first fence body that holds `needle`, or None."""
    for body in fences:
        if needle in body:
            return body
    return None


def run_fence(script, env_paths, cwd=None):
    """(exit, stdout, stderr) of `script` in a fresh `bash -s` whose
    environment holds exactly PATH, VC_ROOT, TMPDIR and STATE_FILE."""
    env = {"PATH": env_paths.get("PATH") or os.environ.get("PATH",
                                                           "/usr/bin:/bin"),
           "VC_ROOT": env_paths["VC_ROOT"], "TMPDIR": env_paths["TMPDIR"],
           "STATE_FILE": env_paths["STATE_FILE"]}
    proc = subprocess.run(["bash", "-s"], input=textwrap.dedent(script),
                          env=env, cwd=cwd or env_paths["TMPDIR"],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=FENCE_TIMEOUT)
    return proc.returncode, proc.stdout, proc.stderr


# --------------------------------------------------------------------------- #
# Capture
# --------------------------------------------------------------------------- #
DRIVERS = {}


def capture_one(repo, situation_id, commit=BASELINE_COMMIT, driver=None,
                tmp_root=None):
    """The normalised outputs of one situation walked at `commit`. Every temp
    directory it makes is removed before it returns or raises."""
    if situation_id not in SITUATIONS:
        raise UsageError("unknown situation: %s" % situation_id)
    scratch = tempfile.mkdtemp(prefix="fc-", dir=tmp_root)
    try:
        pinned = os.path.join(scratch, "pinned")
        work = os.path.join(scratch, "work")
        os.mkdir(pinned)
        os.mkdir(work)
        vc_root = materialize(repo, commit, pinned)
        if driver is None:
            driver_cls = DRIVERS.get(commit)
            if driver_cls is None:
                raise UsageError("no driver walks commit %s" % commit)
            driver = driver_cls()
        outputs = driver.run(situation_id, vc_root, work)
        return normalise_obj(outputs, work, vc_root)
    finally:
        shutil.rmtree(scratch, True)


def capture_record(repo, situation_ids, commit=BASELINE_COMMIT):
    situations = {}
    for sid in situation_ids:
        outputs = capture_one(repo, sid, commit)
        situations[sid] = {"inputs": SITUATIONS[sid]["inputs"],
                           "outputs": outputs,
                           "sha256": canonical_sha256(outputs)}
    return {"schema": SCHEMA, "commit": commit,
            "normalisation": list(NORMALISATION), "situations": situations}


def _parse(argv):
    ap = argparse.ArgumentParser(prog="finalize_capture.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--repo", required=True)
    cap.add_argument("--out", required=True)
    cap.add_argument("--commit", default=BASELINE_COMMIT)
    cap.add_argument("--situation", action="append", choices=list(SITUATIONS))
    return ap.parse_args(argv)


def main(argv=None):
    try:
        args = _parse(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        record = capture_record(args.repo, args.situation or list(SITUATIONS),
                                args.commit)
    except UsageError as exc:
        print("finalize_capture: %s — STOPPING" % exc, file=sys.stderr)
        return 2
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True, indent=1,
                            ensure_ascii=False) + "\n")
    print("wrote %s (%d situation(s))" % (args.out, len(record["situations"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
