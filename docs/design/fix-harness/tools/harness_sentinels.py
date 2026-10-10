"""harness_sentinels.py — plant the owner's unrelated work in a copy and prove
afterwards that the fix run left it exactly as it was.

A preservation run starts with three sentinel lines that stand in for work the
owner had in progress when the fix ran:

  S1  `# sentinel-staged <id>`      in the untouched file, STAGED
  S2  `# sentinel-unstaged <id>`    in the untouched file, unstaged
  S3  `# sentinel-fixed-file <id>`  in the fixed file, unstaged, at least
                                    MIN_HUNK_DISTANCE lines from the fix hunk

So the untouched file's index holds S1 only and its worktree holds S1 + S2;
the fixed file's worktree holds S3 and its index is HEAD.

`plant(copy, recipe)` writes them at the recipe's sites (line numbers in the
committed file) and returns a `SentinelRecord`: the full worktree bytes of
both files, the untouched file's index blob (`git ls-files -s`), the three
sentinel lines, and the fix hunk in worktree coordinates.

`verify(copy, record)` returns `[]` when all of this still holds:
  * the untouched file's worktree bytes equal the recorded bytes;
  * its index blob is unchanged, and neither S1 nor S2 reached HEAD;
  * the fixed file's worktree equals the recorded bytes everywhere outside
    the fix hunk (inside it, the fix may have changed anything), S3 is still
    there, and S3 did not reach HEAD.
Otherwise it returns fixed-template reason lines. A reason may name a file
path; it never quotes file content.

S3 has to sit away from the hunk because the plugin separates the fix from
other unstaged edits in the same file with a three-way merge, and an edit next
to the hunk would conflict with it.

Stdlib only. Git runs as an argv list with a timeout, `cwd=copy.root`, and the
global/system git config switched off. `verify` only reads.
"""

import base64
import json
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_fixture  # noqa: F401  (sys.path setup for the plugin scripts)
import gitfixture  # noqa: E402  (plugin test-support helper: helper_env)

GIT_TIMEOUT = 60
MIN_HUNK_DISTANCE = 5

STAGED_PREFIX = "# sentinel-staged "
UNSTAGED_PREFIX = "# sentinel-unstaged "
FIXED_PREFIX = "# sentinel-fixed-file "

_BYTES_FIELDS = ("untouched_bytes", "fixed_bytes")
_FIELDS = ("untouched_file", "fixed_file", "untouched_bytes", "fixed_bytes",
           "untouched_index_blob", "staged_line", "unstaged_line",
           "fixed_line", "fixed_hunk")


class SentinelError(RuntimeError):
    """The sentinels could not be planted; the message is fixed text."""


class SentinelRecord:
    """What was planted, persisted between `plant` and `verify`."""

    __slots__ = _FIELDS

    def __init__(self, **kwargs):
        missing = [f for f in _FIELDS if f not in kwargs]
        extra = [f for f in kwargs if f not in _FIELDS]
        if missing or extra:
            raise ValueError("sentinel record fields do not match")
        for f in _FIELDS:
            setattr(self, f, kwargs[f])
        self.fixed_hunk = [int(x) for x in self.fixed_hunk]

    def __eq__(self, other):
        return (isinstance(other, SentinelRecord)
                and all(getattr(self, f) == getattr(other, f)
                        for f in _FIELDS))

    def __repr__(self):
        return "SentinelRecord(%s, %s)" % (self.untouched_file,
                                           self.fixed_file)

    def to_json(self):
        doc = {}
        for f in _FIELDS:
            value = getattr(self, f)
            if f in _BYTES_FIELDS:
                value = base64.b64encode(value).decode("ascii")
            doc[f] = value
        return json.dumps(doc, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text):
        doc = json.loads(text)
        if not isinstance(doc, dict):
            raise ValueError("sentinel record is not an object")
        for f in _BYTES_FIELDS:
            if f in doc:
                doc[f] = base64.b64decode(doc[f].encode("ascii"),
                                          validate=True)
        return cls(**doc)


# --------------------------------------------------------------------------- #
# git
# --------------------------------------------------------------------------- #
def _run(root, *args, data=None):
    try:
        return subprocess.run(["git", "--no-optional-locks", *args], cwd=root,
                              env=gitfixture.helper_env(), input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SentinelError("git %s could not run (%s)"
                            % (args[0], type(exc).__name__))


def _git(root, *args):
    proc = _run(root, *args)
    if proc.returncode != 0:
        raise SentinelError("git %s failed (exit %d)"
                            % (args[0], proc.returncode))
    return proc.stdout.decode("utf-8", "replace")


def _index_blob(root, rel):
    """The stage-0 blob sha of `rel` from `git ls-files -s`, or None."""
    out = _git(root, "ls-files", "-s", "--", rel)
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if path == rel and len(parts) == 3 and parts[2] == "0":
            return parts[1]
    return None


def _head_bytes(root, rel):
    """`rel` as committed at HEAD, or None when HEAD has no such file."""
    proc = _run(root, "show", "HEAD:%s" % rel)
    return proc.stdout if proc.returncode == 0 else None


# --------------------------------------------------------------------------- #
# plant
# --------------------------------------------------------------------------- #
def _site(recipe, name, expected_file):
    try:
        site = recipe["sentinels"][name]
        after = site["after_line"]
        path = site["file"]
    except (KeyError, TypeError):
        raise SentinelError("recipe lacks the %s sentinel site" % name)
    if path != expected_file:
        raise SentinelError("the %s sentinel site is in the wrong file" % name)
    if not isinstance(after, int) or isinstance(after, bool) or after < 0:
        raise SentinelError("the %s sentinel site is not a line number" % name)
    return after


def _hunk_distance(after, start, end):
    """Lines between an insertion after line `after` and the hunk [start, end]."""
    if after < start:
        return start - after
    if after > end:
        return after - end
    return 0


def _insert(lines, inserts):
    """`lines` (keepends) with each (after_line, text) inserted; original
    numbering, so later sites go in first."""
    out = list(lines)
    for after, text in sorted(inserts, reverse=True):
        if after > len(out):
            raise SentinelError("a sentinel site is past the end of its file")
        if after > 0 and not out[after - 1].endswith(b"\n"):
            out[after - 1] += b"\n"
        out.insert(after, text.encode("utf-8") + b"\n")
    return out


def plant(copy, recipe):
    """Plant S1 (staged), S2 and S3 (unstaged); return their SentinelRecord."""
    root = copy.root
    untouched = recipe.get("untouched_file")
    fixed = recipe.get("fixed_file")
    if not isinstance(untouched, str) or not isinstance(fixed, str) \
            or untouched == fixed:
        raise SentinelError("recipe must name two different files")
    try:
        start, end = (int(x) for x in recipe["hunk_lines"])
    except (KeyError, TypeError, ValueError):
        raise SentinelError("recipe lacks a usable fix hunk")
    s1 = _site(recipe, "staged", untouched)
    s2 = _site(recipe, "unstaged_untouched", untouched)
    s3 = _site(recipe, "unstaged_fixed", fixed)
    if _hunk_distance(s3, start, end) < MIN_HUNK_DISTANCE:
        raise SentinelError("the fixed-file sentinel is closer than %d lines "
                            "to the fix hunk" % MIN_HUNK_DISTANCE)
    if _git(root, "status", "--porcelain", "--untracked-files=all", "--",
            untouched, fixed).strip():
        raise SentinelError("a sentinel file has uncommitted changes")

    token = uuid.uuid4().hex
    staged_line = STAGED_PREFIX + token
    unstaged_line = UNSTAGED_PREFIX + token
    fixed_line = FIXED_PREFIX + token

    u_path = Path(root, untouched)
    f_path = Path(root, fixed)
    u_lines = u_path.read_bytes().splitlines(keepends=True)
    f_lines = f_path.read_bytes().splitlines(keepends=True)

    u_index = b"".join(_insert(u_lines, [(s1, staged_line)]))
    u_work = b"".join(_insert(u_lines, [(s1, staged_line),
                                        (s2, unstaged_line)]))
    f_work = b"".join(_insert(f_lines, [(s3, fixed_line)]))

    u_path.write_bytes(u_index)
    _git(root, "add", "--", untouched)
    u_path.write_bytes(u_work)
    f_path.write_bytes(f_work)

    blob = _index_blob(root, untouched)
    if blob is None:
        raise SentinelError("the staged sentinel did not reach the index")
    shift = 1 if s3 < start else 0
    return SentinelRecord(
        untouched_file=untouched, fixed_file=fixed,
        untouched_bytes=u_work, fixed_bytes=f_work,
        untouched_index_blob=blob, staged_line=staged_line,
        unstaged_line=unstaged_line, fixed_line=fixed_line,
        fixed_hunk=[start + shift, end + shift])


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #
def _has_line(data, line):
    return line.encode("utf-8") in data.splitlines()


def _read(root, rel):
    p = Path(root, rel)
    if p.is_symlink() or not p.is_file():
        return None
    return p.read_bytes()


def _untouched_reasons(root, record):
    rel = record.untouched_file
    data = _read(root, rel)
    if data is None:
        return ["%s is missing" % rel]
    if data == record.untouched_bytes:
        return []
    reasons = []
    if not _has_line(data, record.staged_line):
        reasons.append("staged sentinel missing from %s" % rel)
    if not _has_line(data, record.unstaged_line):
        reasons.append("unstaged sentinel missing from %s" % rel)
    if not reasons:
        reasons.append("%s changed" % rel)
    return reasons


def _index_blob_reasons(root, record):
    if _index_blob(root, record.untouched_file) != record.untouched_index_blob:
        return ["staged sentinel index blob changed"]
    return []


def _outside_hunk_equal(recorded, current, hunk):
    """Equal everywhere except the hunk lines [start, end] (1-based)."""
    start, end = hunk
    before = recorded[:start - 1]
    after = recorded[end:]
    if len(current) < len(before) + len(after):
        return False
    return (current[:len(before)] == before
            and current[len(current) - len(after):] == after)


def _fixed_reasons(root, record):
    rel = record.fixed_file
    data = _read(root, rel)
    if data is None:
        return ["%s is missing" % rel]
    if not _has_line(data, record.fixed_line):
        return ["fixed-file sentinel missing from %s" % rel]
    if not _outside_hunk_equal(record.fixed_bytes.splitlines(keepends=True),
                               data.splitlines(keepends=True),
                               record.fixed_hunk):
        return ["%s changed outside the fix hunk" % rel]
    return []


def _committed_reasons(root, record):
    reasons = []
    head = _head_bytes(root, record.untouched_file) or b""
    if _has_line(head, record.staged_line):
        reasons.append("staged sentinel was committed")
    if _has_line(head, record.unstaged_line):
        reasons.append("unstaged sentinel was committed")
    head = _head_bytes(root, record.fixed_file) or b""
    if _has_line(head, record.fixed_line):
        reasons.append("fixed-file sentinel was committed")
    return reasons


def verify(copy, record):
    """Reason lines for every way the sentinels drifted; [] when intact."""
    root = copy.root
    return (_untouched_reasons(root, record)
            + _index_blob_reasons(root, record)
            + _fixed_reasons(root, record)
            + _committed_reasons(root, record))
