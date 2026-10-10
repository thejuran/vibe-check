"""harness_seed.py — turn an answer-key record into the pass-1 review state a
fix-loop run starts from, using the plugin's own scorer and shape check.

The seeded state is what a real first review pass would have persisted had it
found exactly the key's defect:

  1. `key_to_finding(key, source)` copies the key's FINDING fields (file, line,
     title, problem, current_code, fix_hint, agent) into one agent-finding item
     and reads the raw facts the scorer needs (`source_window`,
     `canonical_line_content`) from the reviewed file's bytes. Everything else
     in the key — the defect check, the expected commit files, the axis, the
     case id — is harness-only and never leaves the harness.
  2. `seed_state(copy, key, mode)` resolves `changed_line_ranges` from the
     copy's last commit, runs the plugin's `score.py` on that envelope, refuses
     unless the finding survives at band warning or above, wraps the scorer's
     output as pass 1 at the copy's HEAD, writes it atomically to the path the
     plugin's `statepath.resolve` names for the mode, and runs the plugin's
     `state_shape.py --schema future` on the written file.

The scored fields (`orchestrator_score`, `band`, `stable_hash`, `snapshot`, ...)
are therefore the scorer's, never the harness's, and the pass entry is the one
the plugin's schema accepts.

`copy_is_key_free(root)` is the isolation check: the fix agent must never be
able to read answer-key material from the copy it works in.

Stdlib only. Plugin scripts run as `[python, script]` argv lists with a
timeout; finding text travels on stdin, never on argv. Errors are fixed
messages that never echo finding text.
"""

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_fixture  # noqa: E402  (build_copy / CopyInfo, plugin paths)
from harness_fixture import KEYS_DIR, PLUGIN_SCRIPTS_DIR  # noqa: E402

import statepath  # noqa: E402  (plugin: the one state-filename rule)

SCORE_PY = PLUGIN_SCRIPTS_DIR / "score.py"
STATE_SHAPE_PY = PLUGIN_SCRIPTS_DIR / "state_shape.py"
SUBPROCESS_TIMEOUT = 60

MODES = harness_fixture.MODES
# The finding fields an agent would report; the only key fields copied.
FINDING_FIELDS = ("file", "line", "title", "problem", "current_code",
                  "fix_hint", "agent")
BLOCKING_BANDS = ("critical", "warning")
# An agent reports a severity, not a band; the scorer derives the band.
SEVERITY_FOR_BAND = {"critical": "critical", "warning": "high"}
SEED_CONFIDENCE = 90
SEED_CATEGORY = "bug"
REVIEW_COMMAND = "review"
CODEX_OFF = {"status": "off", "reason": None, "verdict": None, "findings": 0}

# Strings that only answer-key records carry. Any of them inside the copy
# means key material crossed into the fix agent's view (D-14).
KEY_ONLY_NEEDLES = (b"defect_check", b"expected_commit_files", b'"axis"')

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


class SeedError(RuntimeError):
    """The seeded state could not be produced; the message is fixed text."""


class SeededState(str):
    """The written state file's path, carrying what the run needs about it.

    A `str` so every caller that wants a path can open it directly.
    `stable_hash` is the scorer's hash of the seeded finding;
    `seeded_identity` is `(file, title)`, the identity the harness answers
    the plugin's cards from.
    """

    def __new__(cls, path, stable_hash, seeded_identity):
        obj = super().__new__(cls, path)
        obj.stable_hash = stable_hash
        obj.seeded_identity = seeded_identity
        return obj


def _source_lines(source):
    if not isinstance(source, (bytes, bytearray)):
        raise SeedError("source must be the reviewed file's bytes")
    try:
        text = bytes(source).decode("utf-8")
    except UnicodeDecodeError:
        raise SeedError("reviewed file is not UTF-8")
    return text.splitlines()


def key_to_finding(key, source):
    """One agent-finding item for `key`, with raw facts read from `source`.

    `source` is the bytes of `key["file"]` as it stands at HEAD. Pure: no I/O.
    """
    if not isinstance(key, dict):
        raise SeedError("key record is not an object")
    for field in FINDING_FIELDS + ("band",):
        if field not in key:
            raise SeedError("key record lacks a finding field: %s" % field)
    for field in ("file", "title", "problem", "current_code", "agent"):
        if not isinstance(key[field], str) or not key[field].strip():
            raise SeedError("key field %s must be a non-empty string" % field)
    if key["band"] not in BLOCKING_BANDS:
        raise SeedError("key band must be critical or warning")
    line = key["line"]
    if not isinstance(line, int) or isinstance(line, bool):
        raise SeedError("key line must be an integer")
    lines = _source_lines(source)
    if not 1 <= line <= len(lines):
        raise SeedError("key line is outside the reviewed file")
    window = lines[max(0, line - 3):line + 2]
    finding = {k: key[k] for k in FINDING_FIELDS}
    finding.update({
        "id": "%s-001" % key["agent"],
        "category": SEED_CATEGORY,
        "cwe": None,
        "severity": SEVERITY_FOR_BAND[key["band"]],
        "agent_confidence": SEED_CONFIDENCE,
        "in_diff": False,
        "intent_doc_match": None,
        "silenced_marker_nearby": False,
        "source_window": window,
        "canonical_line_content": lines[line - 1].rstrip(),
    })
    return finding


def _git(root, *args):
    try:
        proc = subprocess.run(["git", "--no-optional-locks", *args], cwd=root,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=SUBPROCESS_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SeedError("git %s could not run (%s)"
                        % (args[0], type(exc).__name__))
    if proc.returncode != 0:
        raise SeedError("git %s failed (exit %d)" % (args[0], proc.returncode))
    return proc.stdout


def _plugin(script, *args, stdin=None):
    """Run a plugin script as an argv list; JSON goes in on stdin only."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        return subprocess.run([sys.executable, str(script), *args],
                              input=stdin, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True,
                              timeout=SUBPROCESS_TIMEOUT, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SeedError("%s could not run (%s)"
                        % (Path(script).name, type(exc).__name__))


def _changed_ranges(root, base, head, rel):
    """`[[start, end], ...]` of lines `rel` gained in `base..head`."""
    diff = _git(root, "diff", "--no-color", "--no-ext-diff", "-U0",
                base, head, "--", rel)
    ranges = []
    for text in diff.splitlines():
        m = _HUNK_RE.match(text)
        if not m:
            continue
        start = int(m.group(1))
        count = 1 if m.group(2) is None else int(m.group(2))
        if count > 0:
            ranges.append([start, start + count - 1])
    return ranges


def _resolve_path(copy, mode):
    if mode == "gsd":
        rel, reason = statepath.resolve("gsd", phase_id=copy.phase_id)
    else:
        branch = _git(copy.root, "branch", "--show-current").strip()
        rel, reason = statepath.resolve(
            "default", repo=os.path.basename(os.path.realpath(copy.root)),
            branch=branch)
    if rel is None:
        raise SeedError("state path could not be resolved: %s" % reason)
    return os.path.join(copy.root, rel)


def _write_new(path, data):
    """Write `data` to `path` atomically; refuse if `path` already exists."""
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".seed-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        # link() fails if the target exists, so a state is never overwritten.
        try:
            os.link(tmp, path)
        except FileExistsError:
            raise SeedError("a review state already exists at the seed path")
    finally:
        os.unlink(tmp)


def seed_state(copy, key, mode):
    """Seed the pass-1 state for `key` into `copy`; return a SeededState."""
    if mode not in MODES:
        raise ValueError("unknown mode %r (expected one of %s)"
                         % (mode, ", ".join(MODES)))
    if mode == "gsd" and not copy.phase_id:
        raise SeedError("a GSD seed needs the copy's phase id")
    path = _resolve_path(copy, mode)
    if os.path.lexists(path):
        raise SeedError("a review state already exists at the seed path")

    rel = key.get("file") if isinstance(key, dict) else None
    if not isinstance(rel, str) or not re.match(r"^[A-Za-z0-9._/-]+$", rel) \
            or ".." in rel.split("/"):
        raise SeedError("key file is not a safe repository path")
    head = _git(copy.root, "rev-parse", "HEAD").strip()
    if head != copy.head_sha:
        raise SeedError("copy HEAD is not the recorded head")
    source = _git_bytes(copy.root, "%s:%s" % (head, rel))
    finding = key_to_finding(key, source)

    parent = _git(copy.root, "rev-parse", "%s~1" % head).strip()
    envelope = {
        "command": REVIEW_COMMAND,
        "all_mode": False,
        "pass_number": 1,
        "head_sha": head,
        "changed_line_ranges": {rel: _changed_ranges(copy.root, parent,
                                                     head, rel)},
        "reviewed_union": [],
        "file_line_totals": {},
        "carryforward": [],
        "codex": {"status": "off"},
        "findings": [finding],
    }
    proc = _plugin(SCORE_PY, stdin=json.dumps(envelope))
    if proc.returncode != 0:
        raise SeedError("score.py failed (exit %d)" % proc.returncode)
    try:
        scored = json.loads(proc.stdout)
    except ValueError:
        raise SeedError("score.py output is not JSON")
    survivors = [f for f in scored.get("findings", [])
                 if f.get("file") == finding["file"]
                 and f.get("title") == finding["title"]]
    if (not scored.get("scored_by_script") or len(scored["findings"]) != 1
            or len(survivors) != 1
            or survivors[0].get("band") not in BLOCKING_BANDS):
        raise SeedError("the seeded finding did not survive scoring at "
                        "warning or above")

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    pass_entry = {
        "pass_number": 1,
        "head_sha": head,
        "timestamp": timestamp,
        "mode": REVIEW_COMMAND,
        "diff_range": "%s..%s" % (parent, head),
        "agents_run": [finding["agent"]],
        "findings": scored["findings"],
        "filtered": scored.get("filtered", []),
        "codex": dict(CODEX_OFF),
    }
    if scored.get("resolved"):
        pass_entry["resolved"] = scored["resolved"]
    state = {"medium_acknowledgments": {}, "passes": [pass_entry]}
    _write_new(path, json.dumps(state, indent=2, sort_keys=True) + "\n")

    check = _plugin(STATE_SHAPE_PY, path, "--schema", "future")
    if check.returncode != 0:
        os.unlink(path)
        raise SeedError("state_shape.py rejected the seeded state (exit %d)"
                        % check.returncode)
    return SeededState(path, survivors[0]["stable_hash"],
                       (finding["file"], finding["title"]))


def _git_bytes(root, spec):
    try:
        proc = subprocess.run(["git", "--no-optional-locks", "show", spec],
                              cwd=root, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=SUBPROCESS_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SeedError("git show could not run (%s)" % type(exc).__name__)
    if proc.returncode != 0:
        raise SeedError("key file is not in the copy's HEAD")
    return proc.stdout


def _key_paths():
    """Every answer-key file's absolute path, as bytes needles."""
    out = []
    if KEYS_DIR.is_dir():
        for p in sorted(KEYS_DIR.iterdir()):
            if p.is_file():
                out.append(str(p).encode("utf-8"))
                out.append(str(p.resolve()).encode("utf-8"))
    return tuple(dict.fromkeys(out))


def copy_is_key_free(root):
    """True iff no file under `root` carries answer-key material.

    Walks every file, `.git/` and `.turingmind/` included, and looks for the
    key-only field names and any answer-key file's path.
    """
    needles = KEY_ONLY_NEEDLES + _key_paths()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            with open(full, "rb") as fh:
                data = fh.read()
            if any(n in data for n in needles):
                return False
    return True
