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
situation's work directory (the mktemp scratch files the fences make are not
Finalize's writes and are not listed); whether the state file ended up
closed; and a step tally. A situation with more than one walk (the rebuild
that fails a second time, the earlier report that cannot be archived) keeps
each further walk under `legs`, in the same shape. Standard error is
recorded only as present or absent: its text
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
  python3 docs/design/lean-v2.15/tools/finalize_capture.py compare --repo <root> --record <json> --driver helper (--commit <sha> | --root <plugin dir>)
`capture` walks the situations at the pinned commit (or `--commit`) and writes
the record; `verify` re-captures and compares against a committed record.
`compare` walks the same situations on a later version with `HelperWalk`
(one Finalize-inputs fence per attempt, each recorded fault replaced by a
named stand-in) and compares only the outcome fields (`OUTCOME_KEYS`) with
the record; the `steps` and `tally` differences are printed field by field as
the intended ones. It also walks the 2.14.1 tree with the stand-in for the
malformed input, and compares the refusal lines the owner reads on both
versions; a difference in any of these exits 1.
Exit codes: 0 ok; 1 the re-capture differs from the record; 2 unusable input
(unknown commit, unknown situation or leg, unreadable record, a walk that
cannot run as documented, e.g. as root).
"""

import argparse
import getpass
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
    "files_written and files_archived are sorted after normalising, and the "
    "mktemp scratch files under <WORK>/scratch are not listed in them.",
)

# One output schema for all five situations, fixed before any driver exists.
OUTPUT_KEYS = ("steps", "gate", "stop_sentence", "report", "files_written",
               "files_archived", "state_closed", "tally")
# The fields a later version must reproduce byte for byte (Phase 63 D-15);
# `steps` and `tally`, the lists of commands run, are expected to differ.
OUTCOME_KEYS = ("gate", "stop_sentence", "report", "files_written",
                "files_archived", "state_closed")
STEP_KEYS = ("id", "exit", "stdout", "stderr_present")
TALLY_KEYS = ("commands_run", "values_carried", "writes")

SIX_ROW = "scripts/fixtures/iplayarr45-six-row-state.json"
LOOP_STATE = "scripts/fixtures/phase45-loop-state.json"

# fresh-shell-restart: a last-pass fix-obsolete verdict on the six-row
# fixture's one critical finding, bound to a HEAD blob that does not change
# while the owner answers (the 2.14.1 walk's own values).
ARCH_HASH = ("22d360d9c3d841748413b88d41e0840f"
             "d0898a854ee6fa5188f134846a8c7449")
ARCH_FILE = "src/utils/integrationDeadline.ts"
ARCH_BLOB = "blob-pre-card"

# A stamped earlier report, as the 2.14.1 archive walk writes it.
PRIOR_STAMPED_REVIEW = ("# Review\nPhase 54-x\n**Final verdict:** ✅ "
                        "APPROVED\n**State format:** 53\n")

_FLAGS = {"noninteractive": False, "pr_mode": False, "range_mode": False}

# Situation inputs. `prepare` names how the starting state is made from the
# fixture; `attempt_faults` lists, per attempt, what goes wrong with the
# files the model writes (`blobfile: missing` = the printed BLOBFILE is gone
# before the counts step reads it; `gate_input: <text>` = the gate input file
# holds that text instead of the flags object). A situation's `legs` are
# further walks of the same situation, each its own inputs with the listed
# keys overridden. The owner's answers are fixed strings: every shown row
# dismissed with the reason "walk", as the existing 2.14.1 card walk does.
SITUATIONS = {
    "clean-close": {
        "title": "clean close that writes the report",
        "inputs": {
            "fixture": LOOP_STATE,
            "prepare": "dismiss-all",
            "state": ("the fixture with every open finding dismissed through "
                      "the pinned carry_state record_decisions (reason "
                      "'walk'), so no decision is outstanding"),
            "head_blobs": {},
            "flags": _FLAGS,
            "prior_review_md": None,
            "owner_answers": [],
        },
        "legs": {},
    },
    "card-first": {
        "title": "close with open decisions that shows the card first",
        "inputs": {
            "fixture": SIX_ROW,
            "prepare": "copy",
            "state": "the fixture as committed (five critical/warning and "
                     "one medium undecided)",
            "head_blobs": {},
            "flags": _FLAGS,
            "prior_review_md": None,
            "owner_answers": [{"q1": "dismiss 1,2,3,4,5,6 -- walk",
                               "q2": None}],
        },
        "legs": {},
    },
    "one-rebuild": {
        "title": "the one automatic rebuild after a missing input",
        "inputs": {
            "fixture": LOOP_STATE,
            "prepare": "dismiss-all",
            "state": ("the clean-close state; the first attempt's printed "
                      "BLOBFILE is gone before the counts step reads it, so "
                      "the counts fence fails and the one rebuild mints a "
                      "new BLOBFILE, re-counts and gates on a new GATEFILE"),
            "head_blobs": {},
            "flags": _FLAGS,
            "prior_review_md": None,
            "owner_answers": [],
            "attempt_faults": [{"blobfile": "missing"}],
        },
        "legs": {
            "second-failure": {
                "state": ("the clean-close state; the BLOBFILE is gone on "
                          "both attempts, so the rebuild fails too and "
                          "Finalize stops"),
                "attempt_faults": [{"blobfile": "missing"},
                                   {"blobfile": "missing"}],
            },
        },
    },
    "refused-close": {
        "title": "a refused or failed close that writes nothing and archives "
                 "nothing",
        "inputs": {
            "fixture": LOOP_STATE,
            "prepare": "dismiss-all",
            "state": ("the clean-close state; the gate input is malformed on "
                      "both attempts, so Finalize stops with the one stop "
                      "sentence"),
            "head_blobs": {},
            "flags": _FLAGS,
            "prior_review_md": None,
            "owner_answers": [],
            "attempt_faults": [{"gate_input": "not json"},
                               {"gate_input": "not json"}],
        },
        "legs": {
            "unarchivable-report": {
                "state": ("the clean-close state with a stamped earlier "
                          "REVIEW.md in a .turingmind directory that cannot "
                          "be written, so the earlier report cannot be "
                          "archived and Finalize stops before the Write"),
                "attempt_faults": [],
                "prior_review_md": PRIOR_STAMPED_REVIEW,
                "turingmind_read_only": True,
            },
        },
    },
    "fresh-shell-restart": {
        "title": "restart in a fresh shell",
        "inputs": {
            "fixture": SIX_ROW,
            "prepare": "copy",
            "state": ("the fixture with a last-pass fix-obsolete verdict on "
                      "its one critical finding; after the card answer is "
                      "recorded, every later step runs in a fresh shell on "
                      "newly made files: a new BLOBFILE re-fingerprinted "
                      "from HEAD, a recount, a new GATEFILE and the gate"),
            "head_blobs": {ARCH_FILE: ARCH_BLOB},
            "fix_verdicts": {ARCH_HASH: {"verdict": "obsolete",
                                         "agent": "fix",
                                         "reason": "line rewritten",
                                         "verified_blob": ARCH_BLOB}},
            "flags": _FLAGS,
            "prior_review_md": None,
            "owner_answers": [{"q1": "dismiss 1,2,3,4,5 -- walk",
                               "q2": None}],
        },
        "legs": {},
    },
}


def situation_inputs(situation_id, leg=None):
    """The inputs of `situation_id`, or of its named `leg`. Raises
    UsageError for an unknown situation or leg."""
    if situation_id not in SITUATIONS:
        raise UsageError("unknown situation: %s" % situation_id)
    spec = SITUATIONS[situation_id]
    inputs = dict(spec["inputs"])
    if leg is not None:
        if leg not in spec["legs"]:
            raise UsageError("situation %s has no leg %s" % (situation_id,
                                                             leg))
        inputs.update(spec["legs"][leg])
    return inputs

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


def normalise_outputs(outputs, workdir, vc_root=None):
    """A driver's outputs normalised; the file-name lists are sorted after
    normalising, since mktemp suffixes decide their raw order."""
    out = normalise_obj(outputs, workdir, vc_root)
    for key in ("files_written", "files_archived"):
        out[key] = sorted(out[key])
    return out


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
# State preparation (child processes only: nothing pinned is imported here).
# The child code below loads the pinned helpers inside its own interpreter,
# started with -I so neither the caller's environment nor its sys.path leaks in.
# --------------------------------------------------------------------------- #
_PREP_DISMISS_ALL = r"""
import importlib, json, sys
sys.path.insert(0, sys.argv[1])
carry_state = importlib.import_module("carry_state")
with open(sys.argv[2], encoding="utf-8") as fh:
    state = json.load(fh)
counts = carry_state.finalize_counts(state)
hashes = (counts["outstanding_cw_hashes"] + counts["unacknowledged_medium_hashes"]
          + counts["undecided_nv_hashes"])
if not hashes:
    sys.exit(3)
state = carry_state.record_decisions(state, {
    "at_pass": state["passes"][-1]["pass_number"],
    "decisions": [{"stable_hash": h, "decision": "dismiss", "reason": "walk"}
                  for h in hashes]})
if state is None:
    sys.exit(4)
with open(sys.argv[3], "w", encoding="utf-8") as fh:
    json.dump(state, fh)
"""

_PREP_REVIEW_LINES = r"""
import importlib, sys
sys.path.insert(0, sys.argv[1])
finalize_gate = importlib.import_module("finalize_gate")
print(finalize_gate.APPROVED_LINE)
print(finalize_gate.REVIEW_FORMAT_STAMP)
"""


def _child_python(code, args, tmpdir):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "TMPDIR": tmpdir}
    proc = subprocess.run(["python3", "-I", "-c", code] + list(args), env=env,
                          cwd=tmpdir, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=FENCE_TIMEOUT)
    if proc.returncode != 0:
        raise CaptureError("pinned helper child exited %d: %s" % (
            proc.returncode, proc.stderr.strip()))
    return proc.stdout


def prepare_state(vc_root, situation_id, dest, inputs=None):
    """Write the situation's starting state to `dest` from the pinned
    fixture. Raises UsageError for an unknown situation."""
    if inputs is None:
        inputs = situation_inputs(situation_id)
    elif situation_id not in SITUATIONS:
        raise UsageError("unknown situation: %s" % situation_id)
    fixture = os.path.join(vc_root, *inputs["fixture"].split("/"))
    if inputs["prepare"] == "copy":
        shutil.copyfile(fixture, dest)
    elif inputs["prepare"] == "dismiss-all":
        _child_python(_PREP_DISMISS_ALL,
                      [os.path.join(vc_root, "scripts"), fixture, dest],
                      os.path.dirname(dest))
    else:
        raise UsageError("unknown state preparation %r" % inputs["prepare"])
    if inputs.get("fix_verdicts"):
        # Plain JSON editing: the verdicts are bound to the last pass, as
        # the fix agent records them.
        with open(dest, encoding="utf-8") as fh:
            state = json.load(fh)
        last = state["passes"][-1]
        verdicts = {}
        for stable_hash, verdict in inputs["fix_verdicts"].items():
            verdicts[stable_hash] = dict(verdict, head_sha=last["head_sha"],
                                         at_pass=last["pass_number"])
        state["fix_verdicts"] = verdicts
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    return dest


# --------------------------------------------------------------------------- #
# The 2.14.1 driver: walk the Finalize fences
# --------------------------------------------------------------------------- #
_PRINTED_RE = re.compile(r"^([A-Z_]+FILE)=(.+)$", re.M)
_ARCHIVED_RE = re.compile(r"\.archived-|(^|/)REVIEW-[^/]*\.md$|\.migrated-")

COUNTS_CALL = 'carry_state.py" finalize-counts --head-blobs "$BLOBFILE"'
GATE_CALL = 'finalize_gate.py" < "$GATEFILE"'
ROWS_CALL = 'batch_card.py" rows --mode finalize --head-blobs "$BLOBFILE"'
PARSE_CALL = 'batch_card.py" parse --rows "$ROWSFILE" --answer "$ANSWERFILE"'
RECORD_CALL = 'record-decisions --decisions-file "$DECFILE"'
REPORT_CALL = 'batch_card.py" decisions-report < "$STATE_FILE"'
PRIOR_REVIEW_CALL = 'review_archive.py" unstamped --dir .turingmind'
ARCHIVE_STATE_CALL = 'review_archive.py" state --state-file "$STATE_FILE"'
STATE_PRESENT = '[ -f "$STATE_FILE" ]'
FINALIZE_INPUTS_CALL = ('finalize_inputs.py" --state-file "$STATE_FILE" '
                        '--blob-out "$BLOBFILE"')
STATE_REL = ".turingmind/state/format-53/capture.json"
REVIEW_REL = ".turingmind/REVIEW.md"
# The walk's TMPDIR, inside the work directory. The mktemp files the fences
# make there are scratch, not Finalize's writes, so they are not listed in
# `files_written`; they still show in the steps' printed paths.
SCRATCH_DIR = "scratch"
_STOP_RULE_RE = re.compile(r'The stop is exactly one sentence: "([^"\n]+)"')


def stop_sentence(finalize_text):
    """The one stop sentence the rebuild-once rule of `finalize_text`
    prescribes. Raises CaptureError when the rule is absent."""
    found = _STOP_RULE_RE.findall(finalize_text)
    if len(found) != 1 or not found[0].strip():
        raise CaptureError("the Finalize text names %d stop sentences, not 1"
                           % len(found))
    return found[0]


def print_line(name):
    """The fence line that prints a minted temp path, e.g. BLOBFILE=."""
    return "printf '%s=%%s\\n' \"$%s\"" % (name, name)


def _files(root):
    """{rel: sha256} for every regular file under `root`."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.isfile(full) and not os.path.islink(full):
                with open(full, "rb") as fh:
                    found[os.path.relpath(full, root).replace(os.sep, "/")] = \
                        sha256_bytes(fh.read())
    return found


class _Walk:
    """One situation walked fence by fence, the way separate Bash calls run:
    each fence in a fresh shell, a temp path carried only as the printed
    literal pasted over `"$NAME"`, the Write tool simulated by writing the
    file at the printed path."""

    def __init__(self, vc_root, workdir):
        self.vc_root = vc_root
        self.workdir = workdir
        with open(os.path.join(vc_root, *FINALIZE_REL.split("/")),
                  encoding="utf-8") as fh:
            self.finalize_text = fh.read()
        self.fences = extract_fences(self.finalize_text)
        self.tmpdir = os.path.join(workdir, SCRATCH_DIR)
        os.makedirs(self.tmpdir, exist_ok=True)
        self.state_file = os.path.join(workdir, *STATE_REL.split("/"))
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self.env = {"VC_ROOT": vc_root, "TMPDIR": self.tmpdir,
                    "STATE_FILE": self.state_file}
        self.steps, self.gate = [], []
        self.report = None
        self.stop_sentence = None
        self.tally = dict.fromkeys(TALLY_KEYS, 0)
        self.before = {}

    # -- primitives ---------------------------------------------------------
    def fence(self, needle):
        body = fence_holding(self.fences, needle)
        if body is None:
            raise CaptureError("no Finalize fence holds %r" % needle)
        return body

    def step(self, step_id, script, subs=None):
        for name, path in (subs or {}).items():
            ref = '"$%s"' % name
            if ref not in script:
                raise CaptureError("step %s does not read %s" % (step_id, ref))
            script = script.replace(ref, '"%s"' % path)
            script = script.replace('"$%s.' % name, '"%s.' % path)
            self.tally["values_carried"] += 1
        self.tally["commands_run"] += 1
        rc, out, err = run_fence(script, self.env, cwd=self.workdir)
        self.steps.append({"id": step_id, "exit": rc, "stdout": out,
                           "stderr_present": bool(err)})
        return rc, out, err

    def ok(self, step_id, script, subs=None):
        rc, out, err = self.step(step_id, script, subs)
        if rc != 0:
            raise CaptureError("step %s exited %d: %s" % (step_id, rc,
                                                          err.strip()))
        return out

    def mint(self, name, step_id, subs=None):
        out = self.ok(step_id, self.fence(print_line(name)), subs)
        printed = dict(_PRINTED_RE.findall(out))
        if name not in printed:
            raise CaptureError("step %s printed no %s=" % (step_id, name))
        return printed

    def write(self, path, content):
        """The Write tool, in the model's place."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.tally["writes"] += 1

    def write_json(self, path, obj):
        self.write(path, json.dumps(obj))

    # -- Finalize steps ------------------------------------------------------
    def counts_and_gate(self, inputs, fault=None):
        """One attempt of step 1 (HEAD fingerprints), step 2 (counts), the
        gate input and the gate. Returns (blobfile, decision); decision is
        None when the counts fence or the gate fence exited non-zero (the
        halt the rebuild-once rule acts on). `fault` is this attempt's entry
        of the situation's `attempt_faults`."""
        fault = fault or {}
        blob = self.mint("BLOBFILE", "blobfile")["BLOBFILE"]
        if fault.get("blobfile") == "missing":
            # The printed file is gone before the counts step reads it.
            os.remove(blob)
        else:
            self.write_json(blob, inputs["head_blobs"])
        rc, out, _ = self.step("counts", self.fence(COUNTS_CALL),
                               {"BLOBFILE": blob})
        if rc != 0:
            return blob, None
        counts = json.loads(out.strip().splitlines()[0])
        rc, _, _ = self.step("state-present", STATE_PRESENT)
        flags = {"state_file_present": rc == 0,
                 "outstanding_cw": counts["outstanding_cw"],
                 "unacknowledged_medium": counts["unacknowledged_medium"],
                 "undecided_nv": counts["undecided_nv"]}
        flags.update(inputs["flags"])
        gatefile = self.mint("GATEFILE", "gatefile")["GATEFILE"]
        if "gate_input" in fault:
            if fault["gate_input"]:
                self.write(gatefile, fault["gate_input"])
        else:
            self.write_json(gatefile, {"flags": flags})
        rc, out, _ = self.step("gate", self.fence(GATE_CALL),
                               {"GATEFILE": gatefile})
        if rc != 0:
            return blob, None
        try:
            decision = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise CaptureError("the gate printed no decision: %r" % out)
        self.gate.append(decision)
        return blob, decision

    def stop(self, sentence):
        """Finalize stops: the owner reads `sentence` and nothing is
        reported."""
        self.stop_sentence = sentence
        self.report = None

    def card(self, blob, answer):
        """Rows, the card the owner reads, the owner's answer, parse, the
        decisions copy and record-decisions."""
        printed = self.mint("ROWSFILE", "rows", {"BLOBFILE": blob})
        with open(printed["ROWSFILE"], encoding="utf-8") as fh:
            rows = json.load(fh)
        if not rows.get("rows"):
            raise CaptureError("the card has no rows while the gate blocked")
        # What the owner reads: the card text, copied verbatim into Q1.
        self.steps.append({"id": "card", "exit": None,
                           "stdout": rows["card_text"],
                           "stderr_present": False})
        self.write_json(printed["ANSWERFILE"], answer)
        parsed = self.mint("PARSEFILE", "parse",
                           {"ROWSFILE": printed["ROWSFILE"],
                            "ANSWERFILE": printed["ANSWERFILE"]})
        with open(parsed["PARSEFILE"], encoding="utf-8") as fh:
            text = fh.read()
        if not text.strip():
            raise CaptureError("parse refused the owner's answer")
        result = json.loads(text)
        if result.get("payload") is None or result.get("fix"):
            raise CaptureError("the answer does not lead to recording only")
        dec = self.mint("DECFILE", "decfile",
                        {"PARSEFILE": parsed["PARSEFILE"]})["DECFILE"]
        self.ok("record-decisions", self.fence(RECORD_CALL),
                {"DECFILE": dec})

    def close(self):
        """After the gate's `write`: the decisions report, the prior-report
        archive, REVIEW.md, the state archive. When the prior-report archive
        fence fails, Finalize stops with that fence's own message before the
        Write: nothing is written and the state is not archived."""
        out = self.ok("decisions-report", self.fence(REPORT_CALL))
        self.report = json.loads(out.strip().splitlines()[0])
        self.archive_and_write()

    def archive_and_write(self):
        """The prior-report archive, REVIEW.md and the state archive, once
        the report is held."""
        rc, _, err = self.step("prior-review-archive",
                               self.fence(PRIOR_REVIEW_CALL))
        if rc != 0:
            lines = [line for line in err.splitlines()
                     if line.startswith("Finalize stopped")]
            if len(lines) != 1 or lines[0] not in self.finalize_text:
                raise CaptureError("the prior-report archive fence failed "
                                   "without its stop message: %r" % err)
            self.stop(lines[0])
            return
        approved, stamp = _child_python(
            _PREP_REVIEW_LINES, [os.path.join(self.vc_root, "scripts")],
            self.tmpdir).splitlines()[:2]
        # The REVIEW.md prose is the model's; only its verdict and stamp
        # lines are fixed, so the stand-in holds just those.
        self.write(os.path.join(self.workdir, *REVIEW_REL.split("/")),
                   "%s\n%s\n" % (approved, stamp))
        self.ok("archive-state", self.fence(ARCHIVE_STATE_CALL))

    # -- result ------------------------------------------------------------
    def outputs(self):
        after = _files(self.workdir)
        changed = sorted(rel for rel, sha in after.items()
                         if self.before.get(rel) != sha
                         and not rel.startswith(SCRATCH_DIR + "/"))
        archived = sorted(r for r in changed if _ARCHIVED_RE.search(r))
        written = sorted(r for r in changed if not _ARCHIVED_RE.search(r))
        state_closed = (not os.path.exists(self.state_file)
                        and any(r.startswith(STATE_REL + ".archived-")
                                for r in archived))
        return {"steps": self.steps, "gate": self.gate,
                "stop_sentence": self.stop_sentence, "report": self.report,
                "files_written": written, "files_archived": archived,
                "state_closed": state_closed, "tally": dict(self.tally)}


class FenceWalk2141:
    """The 2.14.1 driver: walks `phases/shared/90-finalize.md` fence by
    fence. Phase 63's helper driver must return the same outputs for the same
    situation inputs."""

    NAME = "fence-walk-2.14.1"
    # "One automatic rebuild, then stop": after a failed attempt, step 1 is
    # run again this many times before the stop sentence.
    REBUILDS = 1

    def run(self, situation_id, vc_root, workdir, leg=None):
        inputs = situation_inputs(situation_id, leg)
        read_only = bool(inputs.get("turingmind_read_only"))
        if read_only and os.geteuid() == 0:
            raise UsageError("%s %s needs a directory that cannot be "
                             "written, and root ignores directory "
                             "permissions; run the capture as a normal user"
                             % (situation_id, leg))
        walk = _Walk(vc_root, workdir)
        prepare_state(vc_root, situation_id, walk.state_file, inputs)
        turingmind = os.path.join(workdir, ".turingmind")
        if inputs.get("prior_review_md") is not None:
            with open(os.path.join(workdir, *REVIEW_REL.split("/")), "w",
                      encoding="utf-8") as fh:
                fh.write(inputs["prior_review_md"])
        walk.before = _files(workdir)
        if read_only:
            os.chmod(turingmind, 0o555)
        try:
            getattr(self, "_" + situation_id.replace("-", "_"))(walk, inputs)
        finally:
            if read_only:
                os.chmod(turingmind, 0o755)
        return walk.outputs()

    def gated(self, walk, inputs):
        """Counts and gate under the rebuild-once rule: a failed attempt is
        followed by REBUILDS fresh attempts (new BLOBFILE, recount, new
        GATEFILE), and a further failure stops with the one stop sentence.
        Returns (blobfile, decision), or (None, None) after the stop."""
        faults = inputs.get("attempt_faults", [])
        for attempt in range(self.REBUILDS + 1):
            fault = faults[attempt] if attempt < len(faults) else None
            blob, decision = walk.counts_and_gate(inputs, fault)
            if decision is not None:
                return blob, decision
        walk.stop(stop_sentence(walk.finalize_text))
        return None, None

    def _write_route(self, walk, inputs):
        _, decision = self.gated(walk, inputs)
        if decision is None:
            return
        if decision.get("action") != "write":
            raise CaptureError("the gate returned %r, not write" % decision)
        walk.close()

    def _card_route(self, walk, inputs):
        blob, decision = self.gated(walk, inputs)
        if decision is None or decision.get("action") not in (
                "outstanding-to-phase-5", "medium-ack-loop"):
            raise CaptureError("the first gate returned %r, not a card"
                               % (decision,))
        walk.card(blob, inputs["owner_answers"][0])
        # After the answer, step 3: a NEW BLOBFILE re-fingerprinted from
        # HEAD, re-count, a NEW GATEFILE, the gate once on that literal.
        _, decision = self.gated(walk, inputs)
        if decision is None or decision.get("action") != "write":
            raise CaptureError("the final gate returned %r, not write"
                               % (decision,))
        walk.close()

    _clean_close = _write_route
    _one_rebuild = _write_route
    _refused_close = _write_route
    _card_first = _card_route
    _fresh_shell_restart = _card_route


# --------------------------------------------------------------------------- #
# The 2.15 driver: one Finalize-inputs fence per attempt
# --------------------------------------------------------------------------- #
SWITCH_SLOT = '"<true|false>"'
SWITCH_FLAGS = (("--noninteractive", "noninteractive"),
                ("--pr-mode", "pr_mode"), ("--range-mode", "range_mode"))
# Stand-ins for the 2.14.1 faults, put directly after the fence's
# `printf 'BLOBFILE=%s\n'` line. The gate input file is gone, so a malformed
# gate input becomes a malformed file the attempt depends on: the printed
# BLOBFILE holding `not json`.
FAULT_LINES = {"missing": 'rm -f "$BLOBFILE"',
               "not json": "printf 'not json' > \"$BLOBFILE\""}
# fresh-shell-restart runs in a real git folder: the verdict's file holds
# this text at HEAD, and the verdict is bound to its real blob id.
RESTART_FILE_TEXT = "export const integrationDeadline = 60;\n"
_GIT_DATE = "2026-01-01T00:00:00+00:00"


def helper_fault_line(fault):
    """The shell line standing in for one entry of `attempt_faults`, or None.
    Raises CaptureError for a fault with no stand-in."""
    if not fault:
        return None
    if fault.get("blobfile") in FAULT_LINES:
        return FAULT_LINES[fault["blobfile"]]
    if fault.get("gate_input") == "not json":
        return FAULT_LINES["not json"]
    raise CaptureError("no stand-in for the fault %r" % (fault,))


def insert_after_blob_print(script, line):
    """`script` with `line` put directly after its one BLOBFILE print line,
    at the same indentation."""
    anchor = print_line("BLOBFILE")
    out, found = [], 0
    for text in script.split("\n"):
        out.append(text)
        if text.strip() == anchor:
            out.append(text[:len(text) - len(text.lstrip())] + line)
            found += 1
    if found != 1:
        raise CaptureError("the fence prints BLOBFILE %d times, not 1" % found)
    return "\n".join(out)


def _git_env(home):
    """git with no global or system config and a fixed identity and date."""
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home,
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    for who in ("AUTHOR", "COMMITTER"):
        env["GIT_%s_NAME" % who] = "walk"
        env["GIT_%s_EMAIL" % who] = "walk@example.invalid"
        env["GIT_%s_DATE" % who] = _GIT_DATE
    return env


def _git(args, cwd, env):
    proc = subprocess.run(["git", "-c", "commit.gpgsign=false"] + list(args),
                          cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=GIT_TIMEOUT)
    if proc.returncode != 0:
        raise CaptureError("git %s failed: %s" % (args[0],
                                                  proc.stderr.strip()))
    return proc.stdout


def prepare_git_folder(workdir, files):
    """Make `workdir` a git work tree whose git data lives in a new folder
    beside it (never under it), with each of `files` committed. Returns
    (git directory, {file: real HEAD blob id}). The only git artefact left in
    `workdir` is the one-line `.git` pointer file."""
    parent = os.path.dirname(os.path.abspath(workdir))
    holder = tempfile.mkdtemp(prefix=os.path.basename(workdir) + ".git-",
                              dir=parent)
    git_dir = os.path.join(holder, "git")
    env = _git_env(holder)
    _git(["init", "-q", "--separate-git-dir", git_dir, workdir], parent, env)
    for rel in files:
        path = os.path.join(workdir, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(RESTART_FILE_TEXT)
    _git(["add", "--"] + list(files), workdir, env)
    _git(["commit", "-q", "-m", "walk"], workdir, env)
    blobs = {rel: _git(["rev-parse", "HEAD:" + rel], workdir, env).strip()
             for rel in files}
    return git_dir, blobs


def _bind_real_blobs(inputs, real):
    """`inputs` with every verdict bound to a placeholder blob id rebound to
    the real blob of the same file."""
    swap = {inputs["head_blobs"][rel]: blob for rel, blob in real.items()}
    out = dict(inputs)
    out["fix_verdicts"] = {
        h: dict(v, verified_blob=swap.get(v.get("verified_blob"),
                                          v.get("verified_blob")))
        for h, v in inputs.get("fix_verdicts", {}).items()}
    return out


class _HelperSteps(_Walk):
    """A walk whose counting attempt is the one Finalize-inputs fence."""

    def __init__(self, vc_root, workdir):
        super().__init__(vc_root, workdir)
        # (exit, stderr text) per attempt: kept in memory for the screen-text
        # checks, never added to the record.
        self.attempt_stderr = []
        self.results = []
        self.blobfiles = []
        self.git_dir = None
        self.real_blobs = {}

    def attempt(self, inputs, fault=None):
        """One run of the Finalize-inputs fence in a fresh shell. Returns
        (printed BLOBFILE, {action, reason} or None, exit code)."""
        script = self.fence(FINALIZE_INPUTS_CALL)
        for flag, key in SWITCH_FLAGS:
            slot = "%s %s" % (flag, SWITCH_SLOT)
            if script.count(slot) != 1:
                raise CaptureError("the Finalize-inputs fence has no single "
                                   "%s slot" % flag)
            script = script.replace(slot, '%s "%s"' % (
                flag, "true" if inputs["flags"][key] else "false"))
        line = helper_fault_line(fault)
        if line:
            script = insert_after_blob_print(script, line)
        rc, out, err = self.step("finalize-inputs", script)
        self.attempt_stderr.append((rc, err))
        printed = dict(_PRINTED_RE.findall(out))
        if "BLOBFILE" not in printed:
            raise CaptureError("the Finalize-inputs fence printed no BLOBFILE=")
        blob = printed["BLOBFILE"]
        self.blobfiles.append(blob)
        if rc != 0:
            return blob, None, rc
        try:
            result = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise CaptureError("the Finalize-inputs fence printed no result: "
                               "%r" % out)
        self.results.append(result)
        decision = {"action": result["action"], "reason": result["reason"]}
        self.gate.append(decision)
        return blob, decision, rc

    def close(self):
        """The report is the result's `report` object; the archive, the
        Write and the state archive are the same fences as before."""
        self.report = self.results[-1]["report"]
        self.archive_and_write()


class HelperWalk(FenceWalk2141):
    """The 2.15 driver: the same situations and routes, with each counting
    attempt one Finalize-inputs fence. Exit 5 (the report failed) stops at
    once with that fence's own sentence; any other non-zero exit is a failed
    attempt under the one-rebuild rule."""

    NAME = "helper-walk-2.15"
    WALK = _HelperSteps
    STOP_AT_ONCE = (5,)

    def __init__(self):
        self.last_walk = None

    def prepare(self, situation_id, vc_root, workdir, leg=None):
        """The walk and the inputs it runs on, with the starting files made
        and the `before` snapshot taken."""
        inputs = situation_inputs(situation_id, leg)
        walk = self.WALK(vc_root, workdir)
        self.last_walk = walk
        if inputs.get("head_blobs"):
            walk.git_dir, walk.real_blobs = prepare_git_folder(
                workdir, sorted(inputs["head_blobs"]))
            inputs = _bind_real_blobs(inputs, walk.real_blobs)
        prepare_state(vc_root, situation_id, walk.state_file, inputs)
        if inputs.get("prior_review_md") is not None:
            with open(os.path.join(workdir, *REVIEW_REL.split("/")), "w",
                      encoding="utf-8") as fh:
                fh.write(inputs["prior_review_md"])
        walk.before = _files(workdir)
        return walk, inputs

    def run(self, situation_id, vc_root, workdir, leg=None):
        read_only = bool(situation_inputs(situation_id, leg).get(
            "turingmind_read_only"))
        if read_only and os.geteuid() == 0:
            raise UsageError("%s %s needs a directory that cannot be "
                             "written, and root ignores directory "
                             "permissions; run the capture as a normal user"
                             % (situation_id, leg))
        walk, inputs = self.prepare(situation_id, vc_root, workdir, leg)
        turingmind = os.path.join(workdir, ".turingmind")
        if read_only:
            os.chmod(turingmind, 0o555)
        try:
            getattr(self, "_" + situation_id.replace("-", "_"))(walk, inputs)
        finally:
            if read_only:
                os.chmod(turingmind, 0o755)
        return walk.outputs()

    def gated(self, walk, inputs):
        faults = inputs.get("attempt_faults", [])
        for attempt in range(self.REBUILDS + 1):
            fault = faults[attempt] if attempt < len(faults) else None
            blob, decision, rc = walk.attempt(inputs, fault)
            if decision is not None:
                return blob, decision
            if rc in self.STOP_AT_ONCE:
                walk.stop(self._own_sentence(walk))
                return None, None
        walk.stop(stop_sentence(walk.finalize_text))
        return None, None

    @staticmethod
    def _own_sentence(walk):
        lines = walk.attempt_stderr[-1][1].splitlines()
        if not lines or lines[-1] not in walk.finalize_text:
            raise CaptureError("the Finalize-inputs fence stopped without "
                               "its own sentence: %r" % (lines,))
        return lines[-1]


# The report stage cannot be interrupted from outside between the helper's
# two reads of the state file, so this stand-in runs the real helper (kept
# beside it as finalize_inputs_real.py) and makes the state file `not json`
# right after the count: the helper's own re-read then refuses (exit 5).
_REPORT_STAND_IN = r'''import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
real = __import__("finalize_inputs_real")

_STATE = sys.argv[sys.argv.index("--state-file") + 1]
_COUNT = real.carry_state.finalize_counts


def _count_then_spoil(*args, **kwargs):
    out = _COUNT(*args, **kwargs)
    with open(_STATE, "w", encoding="utf-8") as fh:
        fh.write("not json")
    return out


real.carry_state.finalize_counts = _count_then_spoil
_code, _out = real.run(sys.argv[1:])
if _out:
    sys.stdout.write(_out)
sys.exit(_code)
'''


def report_stand_in_root(vc_root, dest):
    """A copy of the plugin tree `vc_root` under `dest` in which the real
    helper refuses at its report stage. Returns the copy's root."""
    root = os.path.join(dest, "report-stand-in")
    shutil.copytree(vc_root, root,
                    ignore=shutil.ignore_patterns("__pycache__"))
    scripts = os.path.join(root, "scripts")
    os.rename(os.path.join(scripts, "finalize_inputs.py"),
              os.path.join(scripts, "finalize_inputs_real.py"))
    with open(os.path.join(scripts, "finalize_inputs.py"), "w",
              encoding="utf-8") as fh:
        fh.write(_REPORT_STAND_IN)
    return root


# --------------------------------------------------------------------------- #
# Like for like: the candidate's stand-ins given to the 2.14.1 tree
# --------------------------------------------------------------------------- #
class _NotJsonBlob2141Steps(_Walk):
    """The 2.14.1 walk, plus one fault kind it did not record: the printed
    BLOBFILE written as `not json` before the counts step reads it."""

    def __init__(self, vc_root, workdir):
        super().__init__(vc_root, workdir)
        self.attempt_stderr = []

    def counts_and_gate(self, inputs, fault=None):
        if (fault or {}).get("blobfile") != "not json":
            return super().counts_and_gate(inputs, fault)
        blob = self.mint("BLOBFILE", "blobfile")["BLOBFILE"]
        self.write(blob, "not json")
        rc, _, err = self.step("counts", self.fence(COUNTS_CALL),
                               {"BLOBFILE": blob})
        self.attempt_stderr.append((rc, err))
        if rc == 0:
            raise CaptureError("the 2.14.1 counts step took a fingerprint "
                               "file holding 'not json'")
        return blob, None


class LikeForLike2141(FenceWalk2141):
    """The 2.14.1 walk of a write-route situation with every attempt given
    the candidate's stand-in for the malformed gate input. Used only to check
    that the stand-in ends where the recorded fault ended."""

    NAME = "fence-walk-2.14.1-not-json-in-blobfile"
    STAND_IN = {"blobfile": "not json"}

    def __init__(self):
        self.last_walk = None

    def run(self, situation_id, vc_root, workdir, leg=None):
        inputs = situation_inputs(situation_id, leg)
        inputs["attempt_faults"] = [dict(self.STAND_IN)
                                    for _ in range(self.REBUILDS + 1)]
        walk = _NotJsonBlob2141Steps(vc_root, workdir)
        self.last_walk = walk
        prepare_state(vc_root, situation_id, walk.state_file, inputs)
        walk.before = _files(workdir)
        self._write_route(walk, inputs)
        return walk.outputs()


def _short(value, limit=300):
    text = canonical_json(value)
    return text if len(text) <= limit else text[:limit] + "…"


def like_for_like(repo, record, tmp_root=None):
    """Problems with the 2.14.1 tree's refused-close walked with the `not
    json`-in-BLOBFILE stand-in, against the recorded refused-close outcome
    fields. [] when they match."""
    got = capture_one(repo, "refused-close", BASELINE_COMMIT,
                      LikeForLike2141(), tmp_root)
    want = record["situations"]["refused-close"]
    return ["like for like: %s differs: recorded %s, now %s"
            % (key, _short(want[key]), _short(got[key]))
            for key in OUTCOME_KEYS if want[key] != got[key]]


# --------------------------------------------------------------------------- #
# The refusal lines the owner reads (D-18), on both versions
# --------------------------------------------------------------------------- #
def _old_counting_screen(vc_root, workdir, fault):
    walk = _Walk(vc_root, workdir)
    prepare_state(vc_root, "clean-close", walk.state_file)
    blob = walk.mint("BLOBFILE", "blobfile")["BLOBFILE"]
    if fault == "missing":
        os.remove(blob)
    else:
        walk.write(blob, fault)
    rc, _, err = walk.step("counts", walk.fence(COUNTS_CALL),
                           {"BLOBFILE": blob})
    if rc == 0:
        raise CaptureError("the 2.14.1 counts step did not refuse %r" % fault)
    return normalise(err, workdir, vc_root)


def _new_counting_screen(vc_root, workdir, fault):
    walk = _HelperSteps(vc_root, workdir)
    inputs = situation_inputs("clean-close")
    prepare_state(vc_root, "clean-close", walk.state_file, inputs)
    _, decision, rc = walk.attempt(inputs, {"blobfile": fault})
    if decision is not None or rc == 0:
        raise CaptureError("the Finalize-inputs fence did not refuse %r"
                           % fault)
    return normalise(walk.attempt_stderr[-1][1], workdir, vc_root)


def _old_report_screen(vc_root, workdir):
    """The 2.14.1 report fence's stderr when the state file goes bad after
    the gate returned `write`."""
    walk = _Walk(vc_root, workdir)
    inputs = situation_inputs("clean-close")
    prepare_state(vc_root, "clean-close", walk.state_file, inputs)
    _, decision = FenceWalk2141().gated(walk, inputs)
    if (decision or {}).get("action") != "write":
        raise CaptureError("the 2.14.1 gate returned %r, not write"
                           % (decision,))
    with open(walk.state_file, "w", encoding="utf-8") as fh:
        fh.write("not json")
    rc, _, err = walk.step("decisions-report", walk.fence(REPORT_CALL))
    if rc == 0:
        raise CaptureError("the 2.14.1 report fence did not refuse")
    return normalise(err, workdir, vc_root)


def _new_report_screen(vc_root, workdir, tree_dir):
    tree = report_stand_in_root(vc_root, tree_dir)
    walk = _HelperSteps(tree, workdir)
    inputs = situation_inputs("clean-close")
    prepare_state(tree, "clean-close", walk.state_file, inputs)
    _, _, rc = walk.attempt(inputs)
    if rc != 5:
        raise CaptureError("the stand-in helper exited %d, not 5" % rc)
    return normalise(walk.attempt_stderr[-1][1], workdir, tree)


def screen_texts(repo, candidate_root, tmp_root=None):
    """{case: (2.14.1 stderr, candidate stderr)}, normalised, for the two
    counting faults both versions can take (`missing`, `not json`) and for
    the report step (`report`)."""
    scratch = tempfile.mkdtemp(prefix="fc-screen-", dir=tmp_root)
    try:
        def fresh(name):
            path = os.path.join(scratch, name)
            os.mkdir(path)
            return path
        old_root = materialize(repo, BASELINE_COMMIT, fresh("pinned"))
        new_root = copy_tree(candidate_root, fresh("candidate"))
        out = {}
        for n, fault in enumerate(sorted(FAULT_LINES)):
            out[fault] = (
                _old_counting_screen(old_root, fresh("old-%d" % n), fault),
                _new_counting_screen(new_root, fresh("new-%d" % n), fault))
        out["report"] = (_old_report_screen(old_root, fresh("old-report")),
                         _new_report_screen(new_root, fresh("new-report"),
                                            fresh("stand-in")))
        return out
    finally:
        shutil.rmtree(scratch, True)


def counting_screens(repo, candidate_root, tmp_root=None):
    texts = screen_texts(repo, candidate_root, tmp_root)
    return {k: v for k, v in texts.items() if k in FAULT_LINES}


def report_screens(repo, candidate_root, tmp_root=None):
    return screen_texts(repo, candidate_root, tmp_root)["report"]


def screen_matches(old, new):
    """True when the owner reads the same text: byte for byte after
    normalisation."""
    return old == new


# --------------------------------------------------------------------------- #
# Capture
# --------------------------------------------------------------------------- #
DRIVERS = {BASELINE_COMMIT: FenceWalk2141}
# Drivers chosen by name (`compare --driver`), for a tree that is not the
# pinned commit.
DRIVER_NAMES = {"helper": HelperWalk}


def copy_tree(root, dest):
    """Copy the plugin directory `root` into `dest` as the walk's VC_ROOT;
    return the copy's root. Raises UsageError when `root` holds no
    Finalize file."""
    if not os.path.isfile(os.path.join(root, *FINALIZE_REL.split("/"))):
        raise UsageError("%s holds no %s" % (root, FINALIZE_REL))
    copy = os.path.join(dest, *PLUGIN_REL.split("/"))
    shutil.copytree(root, copy, ignore=shutil.ignore_patterns("__pycache__"))
    return copy


def capture_one(repo, situation_id, commit=BASELINE_COMMIT, driver=None,
                tmp_root=None, leg=None, root=None):
    """The normalised outputs of one situation (or one of its legs) walked
    at `commit`, or on a copy of the plugin directory `root` when given.
    `driver` is a driver object, a name from DRIVER_NAMES, or None for the
    commit's own driver. Every temp directory it makes is removed before it
    returns or raises."""
    situation_inputs(situation_id, leg)
    driver = _driver_for(commit, driver)
    scratch = tempfile.mkdtemp(prefix="fc-", dir=tmp_root)
    try:
        pinned = os.path.join(scratch, "pinned")
        work = os.path.join(scratch, "work")
        os.mkdir(pinned)
        os.mkdir(work)
        if root is not None:
            vc_root = copy_tree(root, pinned)
        else:
            vc_root = materialize(repo, commit, pinned)
        outputs = driver.run(situation_id, vc_root, work, leg=leg)
        return normalise_outputs(outputs, work, vc_root)
    finally:
        shutil.rmtree(scratch, True)


def capture_situation(repo, situation_id, commit=BASELINE_COMMIT,
                      driver=None, tmp_root=None, root=None):
    """One situation's record: its main walk's normalised outputs plus
    `legs`, each named leg walked separately in its own directories."""
    situation_inputs(situation_id)
    legs = sorted(SITUATIONS[situation_id]["legs"])
    record = capture_one(repo, situation_id, commit, driver, tmp_root,
                         root=root)
    record["legs"] = {leg: capture_one(repo, situation_id, commit, driver,
                                       tmp_root, leg=leg, root=root)
                      for leg in legs}
    return record


def _driver_for(commit, driver):
    if isinstance(driver, str):
        if driver not in DRIVER_NAMES:
            raise UsageError("unknown driver: %s" % driver)
        return DRIVER_NAMES[driver]()
    if driver is not None:
        return driver
    driver_cls = DRIVERS.get(commit)
    if driver_cls is None:
        raise UsageError("no driver walks commit %s" % commit)
    return driver_cls()


def capture(repo, commit=BASELINE_COMMIT, driver=None, tmp_root=None):
    """The full record: all five situations, in order, walked at `commit`,
    with the normalisation rules and the canonical fingerprint of the
    situations object."""
    driver = _driver_for(commit, driver)
    situations = {sid: capture_situation(repo, sid, commit, driver, tmp_root)
                  for sid in SITUATIONS}
    return {"schema": SCHEMA, "baseline_commit": commit,
            "driver": getattr(driver, "NAME", type(driver).__name__),
            "normalisation": list(NORMALISATION),
            "situations": situations,
            "sha256": canonical_sha256(situations)}


def _sorted_obj(obj):
    if isinstance(obj, dict):
        return {k: _sorted_obj(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_sorted_obj(v) for v in obj]
    return obj


def record_text(record):
    """The record as committed: two-space indent, keys sorted everywhere
    except the situations, which keep their D-07 order, and a trailing
    newline. The fingerprint is over canonical JSON, so this layout does not
    change it."""
    out = _sorted_obj(record)
    situations = record.get("situations")
    if isinstance(situations, dict):
        out["situations"] = {sid: _sorted_obj(situations[sid])
                             for sid in situations}
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- #
# Machine paths
# --------------------------------------------------------------------------- #
MACHINE_PATH_MARKERS = ("/Users/", "/private/", "/tmp/", "/home/")


def current_account():
    """The account name this process runs as, or None."""
    try:
        return getpass.getuser()
    except (KeyError, OSError, ImportError):
        return None


def machine_path_problems(text, account=None):
    """One named problem per machine-specific marker in `text`: a home or
    temp path prefix, or the account name (when longer than three
    characters, as a whole word). `account` defaults to the current
    account; pass "" to skip the account check."""
    problems = ["machine path: %r found" % marker
                for marker in MACHINE_PATH_MARKERS if marker in text]
    if account is None:
        account = current_account() or ""
    if len(account) > 3 and re.search(
            r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(account), text):
        problems.append("the account name of this machine found")
    return problems


# --------------------------------------------------------------------------- #
# Verify
# --------------------------------------------------------------------------- #
def _differences(want, got, path=""):
    """Paths (like `steps[3].stdout`) where `got` differs from `want`."""
    if isinstance(want, dict) and isinstance(got, dict):
        found = []
        for key in sorted(set(want) | set(got)):
            sub = "%s.%s" % (path, key) if path else key
            if key not in got:
                found.append(sub + " missing")
            elif key not in want:
                found.append(sub + " added")
            else:
                found += _differences(want[key], got[key], sub)
        return found
    if isinstance(want, list) and isinstance(got, list):
        found = []
        if len(want) != len(got):
            found.append("%s has %d entries, not %d" % (path or "<root>",
                                                        len(got), len(want)))
        for i, (w, g) in enumerate(zip(want, got)):
            found += _differences(w, g, "%s[%d]" % (path, i))
        return found
    return [] if want == got else [path or "<root>"]


def verify(repo, record_path, driver=None, fresh=None):
    """Problems with the record at `record_path` against a fresh capture at
    the pinned commit (`fresh`, when given, is used instead of capturing
    again). [] when they match; otherwise one line per difference, each
    starting with the situation id, or with `sha256`, `record` or the top-
    level key it concerns. Raises UsageError for an unreadable record."""
    try:
        with open(record_path, encoding="utf-8") as fh:
            text = fh.read()
        record = json.loads(text)
    except (OSError, ValueError) as exc:
        raise UsageError("cannot read the record %s: %s" % (record_path, exc))
    if not isinstance(record, dict) or not isinstance(
            record.get("situations"), dict):
        raise UsageError("%s holds no situations object" % record_path)
    if fresh is None:
        fresh = capture(repo, BASELINE_COMMIT, driver)
    problems = ["record: " + p for p in machine_path_problems(text)]
    for key in ("schema", "baseline_commit", "driver", "normalisation"):
        if record.get(key) != fresh[key]:
            problems.append("%s: %r, the fresh capture has %r"
                            % (key, record.get(key), fresh[key]))
    recorded = record["situations"]
    if record.get("sha256") != canonical_sha256(recorded):
        problems.append("sha256: the stored fingerprint does not match the "
                        "recorded situations")
    sidecar = record_path + ".sha256"
    if os.path.exists(sidecar):
        with open(sidecar, encoding="utf-8") as fh:
            if fh.read().strip() != record.get("sha256"):
                problems.append("sha256: %s does not hold the record's "
                                "fingerprint" % os.path.basename(sidecar))
    for sid in SITUATIONS:
        if sid not in recorded:
            problems.append("%s: missing from the record" % sid)
            continue
        for where in _differences(fresh["situations"][sid], recorded[sid]):
            problems.append("%s: %s differs" % (sid, where))
    for sid in recorded:
        if sid not in SITUATIONS:
            problems.append("%s: not a known situation" % sid)
    if (set(recorded) == set(SITUATIONS)
            and list(recorded) != list(SITUATIONS)):
        problems.append("situations: not in the D-07 order")
    return problems


# --------------------------------------------------------------------------- #
# Compare a later version with the 2.14.1 record (Phase 63 D-15)
# --------------------------------------------------------------------------- #
def capture_candidate(repo, commit=None, root=None, tmp_root=None):
    """{situation: record} for the five situations walked by HelperWalk on
    the tree at `commit` or in the plugin directory `root` (exactly one)."""
    if (commit is None) == (root is None):
        raise UsageError("give exactly one of --commit or --root")
    driver = HelperWalk()
    return {sid: capture_situation(repo, sid, commit, driver, tmp_root,
                                   root=root)
            for sid in SITUATIONS}


def _read_record(record_path):
    try:
        with open(record_path, encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        raise UsageError("cannot read the record %s: %s" % (record_path, exc))
    if not isinstance(record, dict) or not isinstance(
            record.get("situations"), dict):
        raise UsageError("%s holds no situations object" % record_path)
    return record


def _walk_labels(situations):
    """[(label, outputs)] for every main walk and leg, in situation order."""
    out = []
    for sid in SITUATIONS:
        if sid not in situations:
            continue
        out.append((sid, situations[sid]))
        for leg in sorted(situations[sid].get("legs", {})):
            out.append(("%s/%s" % (sid, leg), situations[sid]["legs"][leg]))
    return out


def compare(repo, record_path, commit=None, root=None, fresh=None):
    """(outcome problems, intended differences) of a HelperWalk capture
    against the record. Only OUTCOME_KEYS decide: each differing field is one
    problem naming the walk, the field and both values. `steps` and `tally`
    differences are listed field by field as the intended ones. `fresh`, when
    given, is used instead of capturing again."""
    record = _read_record(record_path)
    if fresh is None:
        fresh = capture_candidate(repo, commit, root)
    recorded = dict(_walk_labels(record["situations"]))
    walked = _walk_labels(fresh)
    problems, intended = [], []
    for label, got in walked:
        want = recorded.get(label)
        if want is None:
            problems.append("%s: missing from the record" % label)
            continue
        for key in OUTCOME_KEYS:
            if key not in want:
                problems.append("%s: %s missing from the record"
                                % (label, key))
            elif _differences(want[key], got[key]):
                problems.append("%s: %s differs: recorded %s, now %s"
                                % (label, key, _short(want[key]),
                                   _short(got[key])))
        old_steps, new_steps = want.get("steps", []), got["steps"]
        if old_steps != new_steps:
            intended.append("%s: steps: before %d (%s), after %d (%s)" % (
                label, len(old_steps),
                ", ".join(s["id"] for s in old_steps), len(new_steps),
                ", ".join(s["id"] for s in new_steps)))
        old_tally = want.get("tally", {})
        for key in TALLY_KEYS:
            if old_tally.get(key) != got["tally"][key]:
                intended.append("%s: tally.%s: before %s, after %s"
                                % (label, key, old_tally.get(key),
                                   got["tally"][key]))
    names = {label for label, _ in walked}
    problems += ["%s: in the record but not walked" % label
                 for label in recorded if label not in names]
    return problems, intended


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _parse(argv):
    ap = argparse.ArgumentParser(prog="finalize_capture.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--repo", required=True)
    cap.add_argument("--out", required=True)
    cap.add_argument("--commit", default=BASELINE_COMMIT)
    ver = sub.add_parser("verify")
    ver.add_argument("--repo", required=True)
    ver.add_argument("--record", required=True)
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("--repo", required=True)
    cmp_.add_argument("--record", required=True)
    cmp_.add_argument("--driver", required=True, choices=sorted(DRIVER_NAMES))
    tree = cmp_.add_mutually_exclusive_group(required=True)
    tree.add_argument("--commit")
    tree.add_argument("--root")
    return ap.parse_args(argv)


def _capture_cmd(args):
    record = capture(args.repo, args.commit)
    text = record_text(record)
    problems = machine_path_problems(text)
    if problems:
        print("RECORD HOLDS A MACHINE PATH — STOPPING", file=sys.stderr)
        for line in problems:
            print("  " + line, file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(args.out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(record["sha256"] + "\n")
    print("wrote %s (%d situations, sha256 %s)"
          % (args.out, len(record["situations"]), record["sha256"]))
    return 0


def _verify_cmd(args):
    problems = verify(args.repo, args.record)
    if problems:
        print("FINALIZE BASELINE DIFFERS — STOPPING")
        for line in problems:
            print("  " + line)
        return 1
    print("finalize baseline matches (%d situations)" % len(SITUATIONS))
    return 0


def _compare_cmd(args):
    record = _read_record(args.record)
    problems, intended = compare(args.repo, args.record, commit=args.commit,
                                 root=args.root)
    scratch = tempfile.mkdtemp(prefix="fc-cmp-")
    try:
        if args.commit is not None:
            os.mkdir(os.path.join(scratch, "tree"))
            candidate = materialize(args.repo, args.commit,
                                    os.path.join(scratch, "tree"))
        else:
            candidate = args.root
        stand_in = like_for_like(args.repo, record)
        screens = screen_texts(args.repo, candidate)
    finally:
        shutil.rmtree(scratch, True)
    walked = {p.split(": ", 1)[0] for p in problems}
    labels = [label for label, _ in _walk_labels(record["situations"])]
    print("compared with %s; driver %s; tree: %s" % (
        os.path.basename(args.record), HelperWalk.NAME,
        "commit %s" % args.commit if args.commit else "the directory given"))
    for label in labels:
        print("%s: %s" % (label, "OUTCOME FIELDS DIFFER" if label in walked
                          else "outcome fields match"))
    print("intended differences (the lists of commands run, D-15):")
    for line in intended:
        print("  " + line)
    print("fault stand-ins and refusal lines:")
    print("  like for like: the 2.14.1 tree's refused-close with `not json` "
          "in the printed BLOBFILE on both attempts: %s"
          % ("outcome fields match the record" if not stand_in
             else "DIFFERS"))
    names = {"missing": "counting refused, printed BLOBFILE removed",
             "not json": "counting refused, `not json` in the printed "
                         "BLOBFILE",
             "report": "report data refused (state file made `not json` "
                       "after the count)"}
    bad_screens = []
    for case in ("missing", "not json", "report"):
        old, new = screens[case]
        same = screen_matches(old, new)
        if not same:
            bad_screens.append(case)
        print("  refusal line, %s: %s" % (
            names[case], "2.14.1 and now identical: " + " / ".join(
                json.dumps(line, ensure_ascii=False)
                for line in new.splitlines()) if same
            else "DIFFERS: 2.14.1 %r, now %r" % (old, new)))
    if problems or stand_in or bad_screens:
        print("FINALIZE OUTCOME DIFFERS — STOPPING")
        for line in problems + stand_in:
            print("  " + line)
        for case in bad_screens:
            print("  refusal line differs: %s" % names[case])
        return 1
    print("finalize outcome fields match (%d situations, %d walks)"
          % (len(SITUATIONS), len(labels)))
    return 0


def main(argv=None):
    try:
        args = _parse(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if args.cmd == "capture":
            return _capture_cmd(args)
        if args.cmd == "compare":
            return _compare_cmd(args)
        return _verify_cmd(args)
    except UsageError as exc:
        print("finalize_capture: %s — STOPPING" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
