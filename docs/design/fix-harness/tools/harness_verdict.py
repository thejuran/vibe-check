"""harness_verdict.py — decide whether a fix-loop run really delivered a
committed repair, and only that repair, without letting the session's code run
with the harness's privileges.

A run is COMPLETE only when all of these hold (FLOW-02):

  1. The COMMITTED tree fixes the defect. `pre_run_head..HEAD` is non-empty and
     the recipe's `defect_check` and `test_cmd` pass on an export of final
     HEAD (`git archive`), never on the working tree. An applied-but-
     uncommitted repair (fixstage exit 3) makes the working tree look fixed
     while HEAD still carries the defect, so the working tree is never judged.
  2. The commits contain only the accepted repair, judged on committed
     CONTENT: every commit's blob of the fixed file equals the defect version
     outside the recipe's `hunk_lines`, no other file changes (per commit and
     net), and the planted sentinels survive.
  3. Finalize really happened: `.turingmind/REVIEW.md` (the path the plugin's
     Finalize writes — a root-level REVIEW.md does not count), exactly one
     archived state, zero outstanding per the plugin's own
     `carry_state.py finalize-counts`, every claimed commit exists, and every
     obligation that ever entered the workflow is accounted for (below).
  4. No answer-key material is in the copy.

WHY THE HEAD CHECKS ARE SANDBOXED. `defect_check` imports and calls the
repaired function, so anything the session put inside the permitted hunk runs
during the verdict. Exporting HEAD isolates git content, not execution. Both
recipe commands therefore run only under `/usr/bin/sandbox-exec` — Seatbelt,
the same mechanism the session's Bash runs under, so one family of profiles
and one failure mode — with a profile that read-denies the source checkout,
the answer keys, the copy, the run's out dir and host credential paths,
denies the network, and a seven-key environment built from scratch.

WHY THE EXPORT IS READ-ONLY AND THE SUITE RUNS SEPARATELY. If committed code
could write the export, `defect_check` could rewrite or delete the exported
tests before `test_cmd` runs, and the suite would "pass" without testing the
committed code. The profile allows writes only under a sibling `runtime/` dir
(HOME, TMPDIR, the Python cache prefix) and denies every write under the
export. Independently, the export is re-hashed against `git ls-tree -r HEAD`
after extraction, after `defect_check` and after `test_cmd`, and the suite is
a separate sandboxed invocation run only on an export proven unchanged.

WHY THE BOUNDARY IS EVALUATED FIRST. Condition 2 is pure git/content and
executes nothing. Running code from a commit that already failed it buys
nothing, so when the boundary fails the HEAD checks are skipped outright.

WHY THERE IS NO FALLBACK. When the sandbox cannot be applied (no
`sandbox-exec`, not darwin, profile rejected) the verdict FAILS with
`head check sandbox unavailable`. No code path runs a recipe command without
the `sandbox-exec` prefix.

FINDING CONSERVATION. Zero outstanding at archive is consistent with a
carry/finalize regression that silently dropped an unresolved row or an
absorbed member. The driver therefore keeps an `ObligationLedger` from the
moment findings first enter the workflow — the seeded state, then every card
and turn — because a ledger started just before Close out would never see a
finding dropped during a rerun. Absorbed `members[].obligation` records are
obligations of their own and are reconciled individually; closing the row that
absorbed one closes nothing for it (the plugin's rule). The plugin's
`open_findings`, `is_closed` and `decision_state` decide what is open and
closed; this module only checks that nothing vanished. Each ledger hash must
end in exactly one disposition:

  resolved      a `passes[].resolved[]` record no older than its first sight
  fix_verified  closed by a last-pass fix verdict whose blob is HEAD's
  decided       a current owner decision carrying a reason
  visible_open  open, non-blocking, visibly retained in the archived last
                pass — an allowed terminal state (owner ruling), counted and
                listed in the record

and two escapes from `visible_open` are closed:

  * BAND DOWNGRADE: an obligation that carried a blocking band (critical,
    warning, medium) at ANY snapshot cannot end open as `low` — it leaves only
    by resolution, fix verification or a reasoned decision.
  * REGRESSION: a finding first seen in a snapshot taken after the fix commit
    moved HEAD (`first_seen.head_sha != pre_run_head`) whose location lies in
    the fixed file inside the repair span in HEAD (lines s..e_head; an
    unparseable line counts as inside — fail closed) must be resolved or
    fix-verified regardless of band; a decision does not clear it. A post-fix
    finding in the fixed file OUTSIDE the span, or inside it but first seen
    before the fix, is a pre-existing issue the rerun surfaced and follows the
    normal rules — that is by design, not a gap.

The seeded finding obeys the regression standard: it must be resolved or
fix-verified, never merely decided.

Stdlib only. Shells out to git, `/usr/bin/sandbox-exec` and the plugin's
`carry_state.py finalize-counts`, always as argv lists with a timeout, never
through a shell. Never writes into the copy. Reasons are fixed templates that
may carry a path, a short sha, a line number or a hash prefix, never finding
text.
"""

import collections
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_fixture  # noqa: E402
import harness_seed  # noqa: E402
import harness_sentinels  # noqa: E402

SANDBOX_EXEC = "/usr/bin/sandbox-exec"
CHECKOUT_ROOT = os.path.realpath(
    os.path.join(str(harness_fixture.PLUGIN_SCRIPTS_DIR), "..", "..", ".."))
CARRY_STATE_PY = os.path.join(str(harness_fixture.PLUGIN_SCRIPTS_DIR),
                              "carry_state.py")
DEFAULT_DENIED_ROOTS = (
    CHECKOUT_ROOT,
    os.path.realpath(str(harness_fixture.KEYS_DIR)),
) + tuple(os.path.expanduser(p) for p in (
    "~/.ssh", "~/.aws", "~/.config/gh", "~/.netrc", "~/.gnupg", "~/.claude",
    "~/.claude.json"))

GIT_TIMEOUT = 60
HEAD_CHECK_TIMEOUT = 120
PLUGIN_TIMEOUT = 60
# sandbox-exec exits 65 with "sandbox-exec: ..." on stderr when it rejects a
# profile (observed on this host for an SBPL syntax error); the command did
# not run.
SANDBOX_REJECTED_EXIT = 65
TIMEOUT_EXIT = 124

FIX_SUBJECT_RE = re.compile(r"^fix\(review-pass-[0-9]+\): ")
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
HEX_SHA_RE = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
CLAIM_RE = re.compile(r"commit_sha=([0-9A-Za-z]*)")
LEDGER_LABELS = ("seed", "card", "turn_end", "owner_command", "final")
DISPOSITIONS = ("resolved", "fix_verified", "decided", "visible_open",
                "downgraded", "regression", "missing", "ambiguous")

Verdict = collections.namedtuple("Verdict", "status reasons dispositions")
Reconciliation = collections.namedtuple("Reconciliation",
                                        "problems dispositions")
RepairSpan = collections.namedtuple("RepairSpan", "path s e_head")


class SandboxUnavailable(Exception):
    """Seatbelt could not be applied; nothing was run."""


class VerdictError(RuntimeError):
    """A git read the verdict depends on failed."""


# --------------------------------------------------------------------------- #
# plugin module (read-only: the plugin decides what is open and closed)
# --------------------------------------------------------------------------- #
_CARRY_STATE = None


def _carry_state():
    global _CARRY_STATE
    if _CARRY_STATE is None:
        spec = importlib.util.spec_from_file_location("carry_state",
                                                      CARRY_STATE_PY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _CARRY_STATE = module
    return _CARRY_STATE


# --------------------------------------------------------------------------- #
# git (read-only; never refreshes the copy's index)
# --------------------------------------------------------------------------- #
def _host_env(**extra):
    """A small explicit environment for the harness's own git and plugin
    calls (never used for a sandboxed command)."""
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "TMPDIR")
           if k in os.environ}
    env.update(extra)
    return env


def _git_env():
    return _host_env(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def _git_run(root, *args):
    try:
        return subprocess.run(["git", "--no-optional-locks", *args], cwd=root,
                              env=_git_env(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerdictError("git %s could not run (%s)"
                           % (args[0], type(exc).__name__))


def _git(root, *args):
    proc = _git_run(root, *args)
    if proc.returncode != 0:
        raise VerdictError("git %s failed (exit %d)"
                           % (args[0], proc.returncode))
    return proc.stdout.decode("utf-8", "replace")


def _blob_bytes(root, rev, path):
    """`path` at `rev`, or None when that revision has no such file."""
    proc = _git_run(root, "show", "%s:%s" % (rev, path))
    return proc.stdout if proc.returncode == 0 else None


def _rev_list(root, pre_run_head, reverse=False):
    args = ["rev-list"] + (["--reverse"] if reverse else []) \
        + ["%s..HEAD" % pre_run_head]
    return _git(root, *args).split()


def _is_under(path, root):
    """True when `path` equals `root` or lies below it (lexical)."""
    root = root.rstrip("/") or "/"
    if root == "/":
        return path.startswith("/")
    return path == root or path.startswith(root + "/")


# --------------------------------------------------------------------------- #
# Condition 2 — repair-only commits, judged on committed content
# --------------------------------------------------------------------------- #
def _subject_ok(subject):
    return bool(FIX_SUBJECT_RE.match(subject))


def _commit_paths(root, sha):
    out = _git(root, "diff-tree", "-z", "--no-commit-id", "--name-only",
               "--no-renames", "-r", sha)
    return [p for p in out.split("\0") if p]


def _commit_files_problems(copy, sha, expected):
    return ["commit %s touches %s outside the accepted repair" % (sha[:7], p)
            for p in _commit_paths(copy.root, sha) if p not in expected]


def _hunk_ok(defect_lines, lines, start, end):
    prefix = start - 1
    suffix = len(defect_lines) - end
    if lines is None or len(lines) < prefix + suffix:
        return False
    return (lines[:prefix] == defect_lines[:prefix]
            and lines[len(lines) - suffix:] == defect_lines[end:])


def repair_boundary_problems(copy, recipe, key, pre_run_head):
    """Reason lines for every way the commits in `pre_run_head..HEAD` exceed
    the accepted repair. Pure git/content: executes nothing."""
    root = copy.root
    expected = set(key.get("expected_commit_files") or ())
    fixed = recipe["fixed_file"]
    start, end = (int(x) for x in recipe["hunk_lines"])
    problems = []
    defect = _blob_bytes(root, pre_run_head, fixed)
    defect_lines = defect.splitlines(keepends=True) if defect is not None \
        else None
    for sha in _rev_list(root, pre_run_head, reverse=True):
        parents = _git(root, "rev-list", "--parents", "-n", "1", sha).split()
        subject = _git(root, "log", "-1", "--format=%s", sha).rstrip("\n")
        if len(parents) != 2 or not _subject_ok(subject):
            problems.append("unexpected commit %s" % sha[:7])
        problems.extend(_commit_files_problems(copy, sha, expected))
        for path in _commit_paths(root, sha):
            if path not in expected:
                continue
            if path != fixed or defect_lines is None:
                problems.append("commit %s changes %s which has no accepted "
                                "repair hunk" % (sha[:7], path))
                continue
            blob = _blob_bytes(root, sha, path)
            lines = blob.splitlines(keepends=True) if blob is not None \
                else None
            if not _hunk_ok(defect_lines, lines, start, end):
                problems.append(
                    "commit %s changes %s outside the accepted repair hunk "
                    "(lines %d-%d)" % (sha[:7], path, start, end))
    net = _git(root, "diff", "-z", "--name-only", "--no-renames",
               pre_run_head, "HEAD")
    for path in [p for p in net.split("\0") if p]:
        if path not in expected:
            problems.append("net touches %s outside the accepted repair"
                            % path)
    return problems


# --------------------------------------------------------------------------- #
# Condition 1 — the committed tree, exported read-only, run under Seatbelt
# --------------------------------------------------------------------------- #
def export_head(copy, dest):
    """Extract `git archive HEAD` into `<dest>/tree`; return that path.

    Creates nothing outside `<dest>/tree` and deletes nothing.
    """
    proc = _git_run(copy.root, "archive", "--format=tar", "HEAD")
    if proc.returncode != 0:
        raise VerdictError("git archive failed (exit %d)" % proc.returncode)
    tree = os.path.join(dest, "tree")
    os.mkdir(tree)
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as tar:
        tar.extractall(tree, filter="data")
    return tree


def _blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def export_matches_head(copy, tree_dir):
    """Problems where `tree_dir` differs from `git ls-tree -r HEAD`.

    Pure comparison: no side effects, no caching. Every HEAD blob must be
    present with identical bytes (a symlink hashes its target string); any
    other file or directory under the export is unexpected.
    """
    out = _git(copy.root, "ls-tree", "-r", "-z", "HEAD")
    head = {}
    problems = set()
    for entry in [e for e in out.split("\0") if e]:
        meta, _, path = entry.partition("\t")
        parts = meta.split()
        if len(parts) != 3:
            continue
        mode, kind, sha = parts
        if kind == "commit":
            problems.add("export contains a submodule")
            continue
        head[path] = (mode, sha)
    dirs = set()
    for path in head:
        parent = os.path.dirname(path)
        while parent:
            dirs.add(parent)
            parent = os.path.dirname(parent)
    seen = set()
    for dirpath, dirnames, filenames in os.walk(tree_dir, followlinks=False):
        for name in sorted(dirnames + filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, tree_dir).replace(os.sep, "/")
            if os.path.islink(full):
                data = os.readlink(full).encode("utf-8", "surrogateescape")
            elif os.path.isdir(full):
                if rel not in dirs:
                    problems.add("export modified: unexpected file %s" % rel)
                continue
            elif os.path.isfile(full):
                with open(full, "rb") as fh:
                    data = fh.read()
            else:
                problems.add("export modified: unexpected file %s" % rel)
                continue
            if rel not in head:
                problems.add("export modified: unexpected file %s" % rel)
                continue
            seen.add(rel)
            if _blob_sha(data) != head[rel][1]:
                problems.add("export modified: %s" % rel)
    for rel in head:
        if rel not in seen:
            problems.add("export modified: %s" % rel)
    return sorted(problems)


def _sbpl_path(path):
    real = os.path.realpath(path)
    return '"%s"' % real.replace("\\", "\\\\").replace('"', '\\"')


def head_sandbox_profile(export_dir, runtime_dir, denied_roots):
    """The Seatbelt profile for the HEAD checks.

    Writes are allowed only under `runtime_dir`; the export is never writable.
    Raises ValueError when the export and the runtime dir nest either way.
    """
    export = os.path.realpath(export_dir)
    runtime = os.path.realpath(runtime_dir)
    if _is_under(export, runtime) or _is_under(runtime, export):
        raise ValueError("the export and the runtime dir must not nest")
    lines = [
        "(version 1)",
        "(allow default)",
        "(deny network*)",
        '(deny file-write* (subpath "/"))',
        # The ONLY writable subpath. Committed code that could write the
        # export could rewrite the exported suite before it runs.
        "(allow file-write* (subpath %s))" % _sbpl_path(runtime),
        '(allow file-write* (literal "/dev/null"))',
    ]
    for root in denied_roots:
        lines.append("(deny file-read* (subpath %s))" % _sbpl_path(root))
    return "\n".join(lines) + "\n"


def run_sandboxed(argv, cwd, profile, runtime_dir, timeout):
    """Run `argv` under `sandbox-exec -p profile` with a scrubbed env.

    Raises SandboxUnavailable when the platform is not darwin, sandbox-exec is
    not executable, it cannot be launched, or it rejects the profile (exit 65
    with `sandbox-exec:` on stderr — the command did not run). Any other
    non-zero exit is the COMMAND failing, which the caller reports as a failed
    check, not as an unavailable sandbox. A timeout returns exit 124.
    """
    if sys.platform != "darwin":
        raise SandboxUnavailable("not darwin")
    if not os.access(SANDBOX_EXEC, os.X_OK):
        raise SandboxUnavailable("sandbox-exec not executable")
    argv = list(argv)
    if argv and argv[0] in ("python3", "python"):
        argv[0] = os.path.realpath(sys.executable)
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": runtime_dir,
        "TMPDIR": runtime_dir,
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": runtime_dir + "/pycache",
    }
    command = [SANDBOX_EXEC, "-p", profile, *argv]
    try:
        proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                              text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            command, TIMEOUT_EXIT, _text(exc.stdout), _text(exc.stderr))
    except OSError as exc:
        raise SandboxUnavailable("sandbox-exec could not run (%s)"
                                 % type(exc).__name__)
    if proc.returncode == SANDBOX_REJECTED_EXIT \
            and "sandbox-exec:" in (proc.stderr or ""):
        raise SandboxUnavailable("profile rejected")
    return proc


def _text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def _has_repair_commit(copy, pre_run_head):
    return bool(_rev_list(copy.root, pre_run_head))


def _restate(problems, stage):
    out = []
    for p in problems:
        prefix = "export modified: "
        out.append(stage + (p[len(prefix):] if p.startswith(prefix) else p))
    return out


def head_check_problems(copy, recipe, pre_run_head, denied_roots=(),
                        execute=True):
    """Condition 1 reasons. The recipe commands run only on a read-only export
    of HEAD, only inside Seatbelt, and only when `execute` is True."""
    problems = []
    if not _has_repair_commit(copy, pre_run_head):
        problems.append("no repair commit")
    if not execute:
        problems.append("head checks skipped: repair boundary failed")
        return problems
    scratch = os.path.realpath(tempfile.mkdtemp(prefix="fixharness-head-"))
    try:
        if _is_under(scratch, os.path.realpath(copy.root)):
            raise VerdictError("the HEAD export scratch dir is inside the copy")
        runtime = os.path.join(scratch, "runtime")
        os.mkdir(runtime)
        os.mkdir(os.path.join(runtime, "pycache"))
        tree = export_head(copy, scratch)
        bad = export_matches_head(copy, tree)
        if bad:
            return problems + _restate(
                bad, "export invalid before defect check: ")
        profile = head_sandbox_profile(
            tree, runtime,
            DEFAULT_DENIED_ROOTS + (copy.root,) + tuple(denied_roots))
        try:
            proc = run_sandboxed(recipe["defect_check"], tree, profile,
                                 runtime, HEAD_CHECK_TIMEOUT)
            if proc.returncode != 0:
                problems.append("defect check failed on HEAD")
            bad = export_matches_head(copy, tree)
            if bad:
                # A suite run on a tampered export proves nothing.
                problems.extend(_restate(
                    bad, "export modified during defect check: "))
                problems.append("tests skipped: export modified")
                return problems
            proc = run_sandboxed(recipe["test_cmd"], tree, profile, runtime,
                                 HEAD_CHECK_TIMEOUT)
            if proc.returncode != 0:
                problems.append("tests failed on HEAD")
            problems.extend(_restate(export_matches_head(copy, tree),
                                     "export modified during tests: "))
        except SandboxUnavailable as exc:
            problems.append("head check sandbox unavailable: %s" % exc)
        return problems
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Condition 3 — Finalize, outstanding counts, claims
# --------------------------------------------------------------------------- #
def _review_md_path(copy):
    return os.path.join(copy.root, ".turingmind", "REVIEW.md")


def _archived_states(copy):
    base = os.path.join(copy.root, ".turingmind", "state")
    return sorted(glob.glob(os.path.join(glob.escape(base), "**",
                                         "*.json.archived-*"),
                            recursive=True))


def _last_pass_records(state):
    """(finding, file) for every last-pass row and member obligation."""
    try:
        findings = state["passes"][-1]["findings"]
    except (KeyError, IndexError, TypeError):
        return []
    out = []
    for f in findings if isinstance(findings, list) else []:
        if not isinstance(f, dict):
            continue
        out.append((f.get("stable_hash"), f.get("file")))
        for m in f.get("members") or []:
            if isinstance(m, dict) and isinstance(m.get("obligation"), dict):
                out.append((m["obligation"].get("stable_hash"), m.get("file")))
    return out


def head_blobs_for(copy, state):
    """{file: HEAD blob} for each last-pass fix verdict's file, bound only when
    the file is unchanged in both the worktree and the index (mirrors
    90-finalize's HEAD-fingerprint step; anything else is omitted)."""
    try:
        last = state["passes"][-1]["pass_number"]
    except (KeyError, IndexError, TypeError):
        return {}
    verdicts = state.get("fix_verdicts") if isinstance(state, dict) else None
    if not isinstance(verdicts, dict):
        return {}
    records = _last_pass_records(state)
    blobs = {}
    for h, v in verdicts.items():
        if not isinstance(v, dict) or v.get("at_pass") != last:
            continue
        files = [f for rh, f in records if rh == h]
        if not files:
            continue
        rel = files[0]
        if not isinstance(rel, str) or not PATH_RE.match(rel) \
                or ".." in rel.split("/"):
            continue
        if _git_run(copy.root, "diff", "--quiet", "HEAD", "--",
                    rel).returncode != 0:
            continue
        if _git_run(copy.root, "diff", "--cached", "--quiet", "--",
                    rel).returncode != 0:
            continue
        proc = _git_run(copy.root, "rev-parse", "HEAD:%s" % rel)
        if proc.returncode == 0:
            blobs[rel] = proc.stdout.decode("ascii", "replace").strip()
    return blobs


def _finalize_counts(copy, state_text, head_blobs):
    fd, path = tempfile.mkstemp(prefix="fixharness-blobs-", suffix=".json")
    try:
        if _is_under(os.path.realpath(path), os.path.realpath(copy.root)):
            raise VerdictError("the head-blobs file is inside the copy")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(head_blobs, fh)
        env = _host_env(PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run(
            [sys.executable, CARRY_STATE_PY, "finalize-counts",
             "--head-blobs", path], input=state_text, capture_output=True,
            text=True, timeout=PLUGIN_TIMEOUT, env=env)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return None


def _outstanding(counts):
    return int(counts["outstanding_cw"]) + int(counts["unacknowledged_medium"])


def _claims(events):
    """Every commit sha the transcript claims was applied/committed; None for
    an `applied` claim that names no commit."""
    out = []

    def walk(value):
        if isinstance(value, str):
            out.extend(CLAIM_RE.findall(value))
        elif isinstance(value, dict):
            if value.get("status") == "applied":
                sha = value.get("commit_sha")
                out.append(sha if isinstance(sha, str) else None)
            elif isinstance(value.get("commit_sha"), str):
                out.append(value["commit_sha"])
            for k, v in value.items():
                if k != "commit_sha":
                    walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                walk(v)
    walk(list(events or ()))
    return out


def _claim_problems(copy, pre_run_head, events):
    commits = _rev_list(copy.root, pre_run_head)
    for claim in _claims(events):
        ok = (isinstance(claim, str) and len(claim) >= 7
              and re.match(r"^[0-9a-fA-F]+$", claim)
              and any(c.startswith(claim.lower()) for c in commits))
        if not ok:
            return ["success claimed for a commit that does not exist"]
    return []


def _finalize_problems(copy, pre_run_head, events):
    """(problems, archived state or None) for Condition 3."""
    problems = []
    review = _review_md_path(copy)
    if not (os.path.isfile(review) and not os.path.islink(review)
            and os.path.getsize(review) > 0):
        problems.append(".turingmind/REVIEW.md missing")
    archived = _archived_states(copy)
    state = None
    if not archived:
        problems.append("state not archived")
    elif len(archived) > 1:
        problems.append("multiple archived states")
    else:
        with open(archived[0], "r", encoding="utf-8") as fh:
            text = fh.read()
        try:
            state = json.loads(text)
        except ValueError:
            state = None
        counts = _finalize_counts(copy, text, head_blobs_for(copy, state)
                                  if state is not None else {})
        if counts is None:
            problems.append("archived state malformed")
            state = None
        else:
            n = _outstanding(counts)
            if n:
                problems.append("outstanding findings at finalize: %d" % n)
    problems.extend(_claim_problems(copy, pre_run_head, events))
    return problems, state


# --------------------------------------------------------------------------- #
# Condition 3b — finding conservation
# --------------------------------------------------------------------------- #
def snapshot_obligations(state_path):
    """The open obligations in the state at `state_path`, READ-ONLY.

    None when the file does not exist (Finalize archived it);
    `{"malformed": True}` when the plugin cannot read it.
    """
    if not os.path.exists(state_path):
        return None
    with open(state_path, "r", encoding="utf-8") as fh:
        try:
            state = json.load(fh)
        except ValueError:
            return {"malformed": True}
    records = _carry_state().open_findings(state)
    if records is None:
        return {"malformed": True}
    return {"pass_number": state["passes"][-1]["pass_number"],
            "hashes": {rec["stable_hash"]: {
                "band": rec["band"], "file": rec.get("file"),
                "line": rec.get("line"),
                "absorbed_into": rec.get("absorbed_into")}
                for rec in records}}


class ObligationLedger:
    """Every obligation that ever entered the workflow, remembered forever.

    `observe` is the single union point: hashes are unioned into `first_seen`
    (fields fixed at first sight) and every band a hash ever carried is
    accumulated in its `bands_seen`. The ledger never judges; it remembers.
    """

    def __init__(self):
        self.first_seen = {}
        self._snapshots = []
        self._seeded = set()

    def observe(self, snapshot, label, head_sha):
        if label not in LEDGER_LABELS:
            raise ValueError("unknown ledger label")
        if not isinstance(head_sha, str) or not HEX_SHA_RE.match(head_sha):
            raise ValueError("head_sha must be a full hex commit id")
        index = len(self._snapshots)
        if snapshot is None:
            self._snapshots.append({"index": index, "label": label,
                                    "head_sha": head_sha, "absent": True})
            return
        if snapshot.get("malformed"):
            self._snapshots.append({"index": index, "label": label,
                                    "head_sha": head_sha, "malformed": True})
            return
        hashes = {h: dict(v) for h, v in snapshot["hashes"].items()}
        self._snapshots.append({"index": index, "label": label,
                                "head_sha": head_sha,
                                "pass_number": snapshot["pass_number"],
                                "hashes": hashes})
        for h, entry in hashes.items():
            if h not in self.first_seen:
                self.first_seen[h] = {
                    "index": index, "pass_number": snapshot["pass_number"],
                    "head_sha": head_sha, "band": entry.get("band"),
                    "file": entry.get("file"), "line": entry.get("line"),
                    "absorbed_into": entry.get("absorbed_into"),
                    "bands_seen": []}
            seen = set(self.first_seen[h]["bands_seen"])
            seen.add(entry.get("band"))
            self.first_seen[h]["bands_seen"] = sorted(
                b for b in seen if isinstance(b, str))

    def mark_seeded(self, hashes):
        hashes = set(hashes)
        unknown = hashes - set(self.first_seen)
        if unknown:
            raise ValueError("a seeded hash was never observed")
        self._seeded |= hashes

    def all_hashes(self):
        return sorted(self.first_seen)

    @property
    def seeded(self):
        return set(self._seeded)

    @property
    def snapshots(self):
        return list(self._snapshots)

    def to_json(self):
        return json.dumps({"first_seen": self.first_seen,
                           "snapshots": self._snapshots,
                           "seeded": sorted(self._seeded)},
                          indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, text):
        doc = json.loads(text)
        led = cls()
        led.first_seen = doc["first_seen"]
        led._snapshots = doc["snapshots"]
        led._seeded = set(doc["seeded"])
        return led


def repair_span_in_head(copy, recipe, pre_run_head):
    """The repair hunk's lines in the final HEAD blob, or None when nothing
    was committed or the fixed file is absent."""
    root = copy.root
    if _git(root, "rev-parse", "HEAD").strip() == pre_run_head:
        return None
    path = recipe["fixed_file"]
    defect = _blob_bytes(root, pre_run_head, path)
    head = _blob_bytes(root, "HEAD", path)
    if defect is None or head is None:
        return None
    start, end = (int(x) for x in recipe["hunk_lines"])
    delta = len(head.splitlines()) - len(defect.splitlines())
    return RepairSpan(path, start, end + delta)


def _post_fix(first, pre_run_head):
    """First seen in a snapshot taken after the fix commit moved HEAD."""
    return pre_run_head is not None and first.get("head_sha") != pre_run_head


def _in_span(first, repair_span):
    if repair_span is None or first.get("file") != repair_span.path:
        return False
    line = first.get("line")
    if not isinstance(line, int) or isinstance(line, bool) or line < 1:
        return True  # an unparseable location in the fixed file fails closed
    return repair_span.s <= line <= repair_span.e_head


def _is_regression(first, pre_run_head, repair_span):
    return _post_fix(first, pre_run_head) and _in_span(first, repair_span)


def _ever_blocking(first, current_band):
    """True when the obligation carried a blocking band at ANY snapshot."""
    return bool(set(first.get("bands_seen") or ())
                & set(_carry_state().BLOCKING_BANDS))


def _closure_subject(record, by_hash):
    """The record whose closure applies: always the record itself — closure
    is never inherited from the row that absorbed a member."""
    return record


def _ambiguous(candidates, same_pass_duplicate, matched, first):
    if "resolved" in candidates and len(candidates) > 1:
        return True
    if same_pass_duplicate:
        return True
    if matched is None:
        return False
    return (matched.get("file") != first.get("file")
            or matched.get("band") not in (first.get("bands_seen") or ()))


_PRIORITY = ("resolved", "fix_verified", "decided", "visible_open")


def _dispose(h, first, by_hash, resolved_by_hash, state, head_blobs, seeded,
             pre_run_head, repair_span):
    """(disposition, [problems]) for one ledger hash."""
    cs = _carry_state()
    short = h[:7]
    candidates = set()
    record = by_hash.get(h)
    subject = None
    if record is not None:
        subject = _closure_subject(record, by_hash)
        if cs.decision_state(subject, state) == "current":
            candidates.add("decided")
        elif cs.is_closed(subject, state, head_blobs):
            candidates.add("fix_verified")
        else:
            candidates.add("visible_open")
    qualifying = [(n, rec) for n, rec in resolved_by_hash.get(h, ())
                  if isinstance(n, int) and n >= first.get("pass_number", 0)]
    if qualifying:
        candidates.add("resolved")
    if not candidates:
        return "missing", ["obligation dropped without decision: %s" % short]
    per_pass = collections.Counter(n for n, _ in qualifying)
    duplicate = any(c > 1 for c in per_pass.values())
    disposition = next(d for d in _PRIORITY if d in candidates)
    matched = qualifying[-1][1] if disposition == "resolved" else record
    if _ambiguous(candidates, duplicate, matched, first):
        return "ambiguous", ["ambiguous obligation match: %s" % short]
    problems = []
    if disposition == "decided":
        decision = (state.get("decisions") or {}).get(subject["stable_hash"])
        if not (isinstance(decision, dict)
                and decision.get("decision") in cs.DECISIONS
                and isinstance(decision.get("reason"), str)
                and decision["reason"].strip()):
            problems.append("obligation decision without reason: %s" % short)
    if disposition in ("decided", "visible_open") \
            and _is_regression(first, pre_run_head, repair_span):
        return "regression", problems + [
            "regression finding not resolved: %s" % short]
    if disposition == "visible_open":
        band = record.get("band")
        if band in cs.BLOCKING_BANDS:
            problems.append("obligation open at archive: %s" % short)
        elif _ever_blocking(first, band):
            return "downgraded", problems + [
                "obligation downgraded without decision: %s" % short]
    return disposition, problems


def reconcile_obligations(ledger, archived_state, head_blobs,
                          pre_run_head=None, repair_span=None):
    """Map every ledger hash to exactly one disposition against the archived
    state; problems for anything missing, ambiguous, unreasoned, downgraded,
    regressed, or a seeded finding not verified resolved."""
    cs = _carry_state()
    problems = []
    for snap in ledger.snapshots:
        if snap.get("malformed"):
            problems.append("state malformed at snapshot %d" % snap["index"])
    records = cs.open_findings(archived_state)
    if records is None:
        return Reconciliation(problems + ["archived state malformed"], {})
    by_hash = {r["stable_hash"]: r for r in records}
    resolved_by_hash = collections.defaultdict(list)
    for p in archived_state.get("passes", []):
        for rec in p.get("resolved") or []:
            if isinstance(rec, dict) and isinstance(rec.get("stable_hash"),
                                                    str):
                resolved_by_hash[rec["stable_hash"]].append(
                    (p.get("pass_number"), rec))
    dispositions = {}
    seeded = ledger.seeded
    for h in ledger.all_hashes():
        first = ledger.first_seen[h]
        disposition, found = _dispose(h, first, by_hash, resolved_by_hash,
                                      archived_state, head_blobs, seeded,
                                      pre_run_head, repair_span)
        dispositions[h] = disposition
        problems.extend(found)
        if h in seeded and disposition not in ("resolved", "fix_verified"):
            problems.append("seeded finding not verified resolved: %s"
                            % h[:7])
    return Reconciliation(problems, dispositions)


def _conservation(copy, recipe, ledger, state, pre_run_head):
    if ledger is None:
        return ["obligation ledger missing"], {}
    if not ledger.all_hashes():
        return ["obligation ledger empty"], {}
    if state is None:
        return [], {}
    span = repair_span_in_head(copy, recipe, pre_run_head)
    rec = reconcile_obligations(ledger, state, head_blobs_for(copy, state),
                                pre_run_head, span)
    return list(rec.problems), dict(rec.dispositions)


# --------------------------------------------------------------------------- #
# the verdict
# --------------------------------------------------------------------------- #
def verdict(copy, recipe, key, sentinel_record_or_None, transcript_events,
            pre_run_head, denied_roots=(), ledger=None):
    """COMPLETE only when every condition holds; otherwise FAILED with every
    reason (no short-circuit beyond skipping execution)."""
    # Committed code executes with the harness's privileges unless contained;
    # never run code from a commit that already failed the repair boundary.
    boundary = repair_boundary_problems(copy, recipe, key, pre_run_head)
    if sentinel_record_or_None is not None:
        boundary += harness_sentinels.verify(copy, sentinel_record_or_None)
    head = head_check_problems(copy, recipe, pre_run_head,
                               denied_roots=denied_roots,
                               execute=not boundary)
    reasons = []
    if pre_run_head != copy.head_sha:
        reasons.append("pre-run head mismatch")
    reasons += boundary + head
    finalize, state = _finalize_problems(copy, pre_run_head,
                                         transcript_events)
    reasons += finalize
    conservation, dispositions = _conservation(copy, recipe, ledger, state,
                                               pre_run_head)
    reasons += conservation
    if not harness_seed.copy_is_key_free(copy.root):
        reasons.append("key material found in copy")
    return Verdict("FAILED" if reasons else "COMPLETE", reasons, dispositions)
