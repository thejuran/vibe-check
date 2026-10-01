"""batchsnap.py — the batch lifecycle mechanism for Phase 40 (D-06, DIET-04).

D-06 says restructure batches are independently revertable; DIET-04 says each
batch is validated before the next lands. Both were claims in prose with no
executable procedure behind them. This module is the procedure: build a pinned
immutable snapshot, run against THAT, record the verdict, then advance or revert
a recorded commit set.

Three properties, each mechanical rather than documentary:

1. **A batch is never observed mid-construction (F17).** Work happens on the
   working tree, but the owner only ever launches against an immutable SNAPSHOT:
   a `git worktree` checked out at a recorded batch-complete commit, with the
   write bits cleared and a MANIFEST carrying a sha256 of every plugin file. A
   session reads phase files LAZILY, minutes into a run, so a clean-tree check at
   launch would prove nothing — the tree can change under it. `verify` re-hashes
   before every run, so a snapshot that drifted is caught.

2. **The rollback unit is an ALLOWLIST over recorded identities (F18, R3).**
   `BATCH_PLANS` names plan ids. `PLAN-COMMITS.json` maps plan ids to the shas
   each plan recorded FOR ITSELF — the plan that made the commit is the only
   thing that knows its identity, so recording is a write, never an inference.
   There is no commit-subject heuristic anywhere in this module, because the
   obvious one was provably wrong in both directions: 40-01's ledger commit
   subject carries no plan tag and it touches a file under `plugins/vibe-check/`,
   so a subject-or-path selector would have swept the append-only SUPERSESSIONS
   ledger into batch 1's revert set — destroying evidence and adding a third
   commit to a path whose own gate requires exactly two.

3. **Advancement consumes evidence (F10).** `check_pass_artifact` validates the
   owner's recorded PASS artifact; the barrier task in each following plan runs it
   and halts on absence, malformation, or FAIL.

**The two roots are NOT the same path and must never be conflated (R2).** A
snapshot worktree is a FULL-REPO checkout and the plugin lives at
`plugins/vibe-check`, so:

    snapshot_root = <SNAP_ROOT>/batch<N>-<short>          (the worktree itself)
    plugin_root   = <snapshot_root>/plugins/vibe-check    (where plugin.json is)

`plugin_root` is the ONLY value that may be passed to `claude --plugin-dir`.
Passing `snapshot_root` loads NO plugin, so every run would silently exercise the
installed cache instead of the batch under test — an unrelated measurement that
looks exactly like a real one. `build` refuses a snapshot lacking
`plugin_root/.claude-plugin/plugin.json`, both roots are recorded in the manifest
as separate keys, both are printed labelled, and `verify` prints `plugin_root:` as
its LAST line so the launch argument always comes from a just-verified snapshot
rather than being retyped.

FL-01 (R5) — **sealing is the LAST action.** `build` runs the completeness check,
then the suite, then resolves the commit set, and only THEN hashes, writes the
manifest, and clears the write bits. Nothing is hashed until every validation that
can mutate the tree has finished. `pytest` writes `__pycache__`/`.pyc` into the
snapshot, so generated files are named in `HASH_EXCLUDE` and that list is RECORDED
INSIDE the manifest — `verify` uses the list the build used, not a module constant
that may have drifted since.

I/O: stdlib only, imports exactly {argparse, hashlib, json, os, re, subprocess,
sys}; every `subprocess.run` carries `timeout=120`. GATE semantics (D-13): exit 0
clean, 1 on any assertion failure, 2 on a usage error or an unreadable input.
Callers branch on the EXIT CODE, never by parsing stdout.

    python3 batchsnap.py build  --batch <1|2|3|4|5|6> --commit <sha> --recorded <path>
    python3 batchsnap.py verify --snap <snapshot_root|plugin_root>
    python3 batchsnap.py commit-set   --batch <N> --recorded <path>
    python3 batchsnap.py record-commit --plan <id> --sha <sha> --recorded <path>
    python3 batchsnap.py check-pass --file <PASS.json> [--expect-commit <sha>]
    python3 batchsnap.py drop --snap <snapshot_root>

Refusal reasons name plugin-internal PATHS (which is fine and necessary) but never
echo repo CONTENT: snapshot files carry text derived from attacker-authored diffs.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

# Snapshots live OUTSIDE the repo so they can never be committed, and outside
# /tmp so they survive a reboot mid-batch.
SNAP_ROOT = os.path.expanduser("~/.vibe-check-snapshots")

# The plugin is NOT at the repo root (R2). A worktree is a full-repo checkout, so
# this subdir is what turns snapshot_root into the launchable plugin_root.
PLUGIN_SUBDIR = "plugins/vibe-check"

# The git TREE of docs/design/b3-ground-truth/runs-v2.10 holding the complete
# Phase-38 baseline. A TREE hash, not a commit: stable under rebase, and it is
# what "the sealed baseline is intact" actually means. The previously-cited
# commit 633f1dd predates the archives entirely and would have refused valid
# evidence (F12).
ARCHIVE_TREE = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a"
ARCHIVE_PATH = "docs/design/b3-ground-truth/runs-v2.10"

# The rollback units (D-06). An ALLOWLIST of plan ids, not a filter (R3): every id
# NOT listed for the requested batch is outside that unit BY CONSTRUCTION.
BATCH_PLANS = {
    1: ("40-02", "40-03", "40-04", "40-05", "40-07", "40-12", "40-13"),
    2: ("40-08", "40-10"),
    3: ("40-11",),
    # Phase 41 Wave-1 scorer commits (B-SEV, B-REWEIGHT, H-LANE) — the SCORER-05
    # rollback unit.
    4: ("41-04", "41-05", "41-06"),
    # Phase 43 launch-gate fix (file-owned Codex collection) — the ONE
    # measured-surface change before the post-change measurement.
    5: ("43-01",),
    # Phase 43 conditional prompts-only retune (D-05); built only on a MISS.
    6: ("43-06",),
}

# Structurally excluded from every rollback unit, ASSERTED rather than described
# (R3) — commit_set raises if any sha it is about to emit is attributed to one of
# these, so the exclusion cannot be lost to a typo in BATCH_PLANS.
#   40-01  writes the append-only SUPERSESSIONS ledger and touches
#          plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md. Reverting it would
#          destroy evidence, and a third verifier commit would break the ledger's
#          own exactly-two-commit gate.
#   40-06  this module: the rollback tooling. Reverting the tooling while using it
#          to revert something is self-defeating.
#   40-09  the owner run checklist — same tooling argument.
#   40-14  the closing record.
#   41-01  the replay manifest + SUPERSESSIONS ledger evidence.
#   41-02  the replay tooling (replay.py) — same tooling argument as 40-06.
#   41-03  the B-REWEIGHT method record (calibrate.py + CALIBRATION-v2.10.md).
#   41-07  the owner spot-check runbook and this module's batch-4 generalization.
#   41-08  the closing record.
#   43-02  the measurement tooling (lanearchive.py, score43.py, this extension).
#   43-03  the owner runbook, run notes and the snapshot record.
#   43-04  the first-pass run evidence.
#   43-05  the scoring worksheet and the recorded verdict.
#   43-07  the RESULTS section and the closing record.
NEVER_REVERT = ("40-01", "40-06", "40-09", "40-14",
                "41-01", "41-02", "41-03", "41-07", "41-08",
                "43-02", "43-03", "43-04", "43-05", "43-07")

# Every Phase-40, Phase-41 and Phase-43 plan id, so record-commit refuses a
# typo'd or foreign id.
KNOWN_PLANS = (tuple("40-%02d" % n for n in range(1, 15))
               + tuple("41-%02d" % n for n in range(1, 9))
               + tuple("43-%02d" % n for n in range(1, 8)))

# FL-01: generated files. pytest writes these INTO the snapshot during build's
# suite check and again whenever anything runs in the snapshot, so they are
# neither hashed at build nor compared at verify. The list is recorded inside the
# manifest so verify uses exactly what the build used.
HASH_EXCLUDE = ("__pycache__/", "*.pyc", ".pytest_cache/")

# The lazy-read instruction form 40-08 establishes (Pattern 8). Written to match
# BOTH shapes so it keeps working across the F2 change: the ${CLAUDE_PLUGIN_ROOT}
# token survives only in loader-processed files (commands/, agents/) on the two
# head Read paths, while every nested read under phases/ uses the RESOLVED
# $VC_ROOT value. Captures the path relative to the plugin root.
READ_INSTRUCTION = re.compile(
    r"Read\s+(?:\*\*)?"
    r"(?:\$\{CLAUDE_PLUGIN_ROOT\}|\$VC_ROOT)/"
    r"([A-Za-z0-9._/-]+\.md)")

MANIFEST_NAME = "MANIFEST.json"

_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "fixtures", "batch-manifest-schema.json")


class BatchError(Exception):
    """Any refusal. The CLI turns it into exit 1 (GATE semantics, D-13)."""


def load_schema(path=None):
    with open(path or _SCHEMA_PATH) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _git(repo, *args):
    """git in `repo`; returns the CompletedProcess (callers check returncode)."""
    return subprocess.run(["git", *args], cwd=repo, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, timeout=120)


def _git_out(repo, *args):
    proc = _git(repo, *args)
    if proc.returncode != 0:
        raise BatchError("git %s failed: %s" % (args[0], proc.stdout.strip()))
    return proc.stdout.strip()


def is_excluded(relpath, exclude=None):
    """Is `relpath` a generated file the manifest ignores? (FL-01)

    `exclude` defaults to the module constant but verify passes the list RECORDED
    IN THE MANIFEST, so a snapshot is always judged by the rules its build used.
    """
    parts = relpath.replace(os.sep, "/").split("/")
    for pattern in (exclude if exclude is not None else HASH_EXCLUDE):
        if pattern.endswith("/"):
            if pattern[:-1] in parts:
                return True
        elif pattern.startswith("*."):
            if parts[-1].endswith(pattern[1:]):
                return True
        elif parts[-1] == pattern:
            return True
    return False


def read_targets(text):
    """Every plugin-root-relative path a lazy-read instruction points at."""
    return READ_INSTRUCTION.findall(text)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_files(plugin_root, exclude=None):
    """Plugin-root-relative paths of every hashable file, sorted.

    Paths are relative to plugin_root (never to snapshot_root) so a manifest is
    comparable across snapshot locations.
    """
    out = []
    for root, dirs, files in os.walk(plugin_root):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, plugin_root).replace(os.sep, "/")
            if is_excluded(rel, exclude):
                continue
            out.append(rel)
    return out


def _chmod_ro(tree, plugin_root, exclude=None):
    """Seal the tree: clear write bits ONLY.

    Never touch read or execute — stripping x would make directories
    untraversable and verify could not re-hash them.

    Excluded paths (FL-01: `__pycache__`, `.pyc`, `.pytest_cache`) are left
    WRITABLE and so is any directory containing them. They carry no integrity
    claim — verify neither hashes nor permission-checks them — and sealing them
    would break the snapshot for its actual purpose: anything the owner runs
    inside it (pytest, a review) regenerates those caches, and a read-only cache
    turns a legitimate run into a permission error.
    """
    for root, dirs, files in os.walk(tree, topdown=False):
        for name in files + dirs:
            p = os.path.join(root, name)
            if os.path.islink(p):
                continue
            rel = os.path.relpath(p, plugin_root).replace(os.sep, "/")
            if not rel.startswith("..") and is_excluded(rel, exclude):
                continue
            mode = os.stat(p).st_mode
            os.chmod(p, mode & ~0o222)
    os.chmod(tree, os.stat(tree).st_mode & ~0o222)


def _chmod_rw(tree):
    for root, dirs, files in os.walk(tree, topdown=False):
        for name in files + dirs:
            p = os.path.join(root, name)
            if os.path.islink(p):
                continue
            os.chmod(p, os.stat(p).st_mode | 0o200)
    os.chmod(tree, os.stat(tree).st_mode | 0o200)


def plugin_root_of(snapshot_root):
    return os.path.join(snapshot_root, PLUGIN_SUBDIR)


def normalize_snap(path):
    """Accept either root and return snapshot_root (R2).

    `build` prints both, and a reader may paste either. A path that is neither is
    a usage error, not a silent guess.
    """
    path = os.path.abspath(os.path.expanduser(path))
    suffix = os.sep + PLUGIN_SUBDIR.replace("/", os.sep)
    if path.endswith(suffix):
        candidate = path[: -len(suffix)]
        if os.path.isfile(os.path.join(candidate, MANIFEST_NAME)):
            return candidate
    if os.path.isfile(os.path.join(path, MANIFEST_NAME)):
        return path
    return None


# ---------------------------------------------------------------------------
# record-commit / commit-set  (F18, R3)
# ---------------------------------------------------------------------------

def record_commit(repo, plan_id, sha, recorded):
    """Append (plan_id, sha) to PLAN-COMMITS.json. Exit-code semantics: 0/1.

    Recording is a WRITE performed by the plan that made the commit — the only
    thing that knows its own identity. Recording a NEVER_REVERT plan's commit is
    legitimate and sometimes necessary; what NEVER_REVERT forbids is EMISSION
    into a revert set, which commit_set asserts.
    """
    if plan_id not in KNOWN_PLANS:
        sys.stderr.write("refused: unknown plan id: %s\n" % plan_id)
        return 1
    proc = _git(repo, "rev-parse", "--verify", "%s^{commit}" % sha)
    if proc.returncode != 0:
        sys.stderr.write("refused: commit does not exist in this repo\n")
        return 1
    full = proc.stdout.strip()

    data = {}
    if os.path.isfile(recorded):
        try:
            with open(recorded) as fh:
                data = json.load(fh)
        except ValueError:
            sys.stderr.write("refused: %s is not valid JSON\n" % recorded)
            return 1
        if not isinstance(data, dict):
            sys.stderr.write("refused: %s is not an object\n" % recorded)
            return 1

    for other, shas in data.items():
        if full in shas and other != plan_id:
            sys.stderr.write("refused: %s is already recorded under plan %s\n"
                             % (full, other))
            return 1

    entries = data.setdefault(plan_id, [])
    if full in entries:
        return 0  # idempotent: a re-run of a plan's final task is safe
    entries.append(full)

    parent = os.path.dirname(os.path.abspath(recorded))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(recorded, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return 0


def commit_set(repo, batch, recorded):
    """The batch's runtime commit set, newest-first — i.e. REVERT ORDER.

    Selection is by recorded identity only. Then four assertions, each raising
    BatchError naming the offender:
      * no emitted sha is attributed to a NEVER_REVERT plan (R3);
      * every plan in BATCH_PLANS[batch] has at least one recorded sha (a batch
        closing with an unrecorded plan is a recording failure, not an empty
        revert set);
      * every emitted sha exists in the repo;
      * no sha is emitted twice.
    """
    if batch not in BATCH_PLANS:
        raise BatchError("unknown batch: %r (known: %s)"
                         % (batch, ", ".join(str(b) for b in sorted(BATCH_PLANS))))
    if not os.path.isfile(recorded):
        raise BatchError("recorded commit file not found: %s" % recorded)
    try:
        with open(recorded) as fh:
            data = json.load(fh)
    except ValueError as exc:
        raise BatchError("recorded commit file is not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise BatchError("recorded commit file is not an object")

    plans = BATCH_PLANS[batch]

    # NEVER_REVERT is asserted from the INSIDE: a typo that puts a protected plan
    # into BATCH_PLANS fails the command instead of silently reverting evidence.
    #
    # This runs BEFORE the recording-completeness check on purpose. A protected
    # plan usually has no recorded sha, so completeness-first would report it as
    # merely "unrecorded" — sending the owner off to record the very commit that
    # must never enter a revert set. The allowlist being wrong outranks a
    # recording gap.
    protected = [p for p in plans if p in NEVER_REVERT]
    if protected:
        raise BatchError(
            "refusing to emit commits for %s: in NEVER_REVERT %s — batch %d's "
            "allowlist is wrong" % (", ".join(protected), list(NEVER_REVERT), batch))

    missing = [p for p in plans if not data.get(p)]
    if missing:
        raise BatchError(
            "batch %d is incomplete: no recorded commit for %s — a batch cannot "
            "close with an unrecorded plan" % (batch, ", ".join(missing)))

    shas = []
    for plan in plans:
        for sha in data[plan]:
            proc = _git(repo, "cat-file", "-e", "%s^{commit}" % sha)
            if proc.returncode != 0:
                raise BatchError("recorded sha does not exist in this repo: %s "
                                 "(plan %s)" % (sha, plan))
            if sha in shas:
                raise BatchError("sha recorded twice: %s" % sha)
            shas.append(sha)

    # Belt and braces: nothing emitted may be attributed to a protected plan, even
    # if it reached BATCH_PLANS by some other route.
    for plan in NEVER_REVERT:
        for sha in data.get(plan, []):
            if sha in shas:
                raise BatchError("refusing to emit %s: recorded under NEVER_REVERT "
                                 "plan %s" % (sha, plan))

    # Newest-first: the owner pastes this straight into `git revert --no-commit`
    # and the order is already correct.
    order = _git_out(repo, "rev-list", "--topo-order", "HEAD").splitlines()
    rank = {sha: i for i, sha in enumerate(order)}
    unknown = [s for s in shas if s not in rank]
    if unknown:
        raise BatchError("recorded sha is not an ancestor of HEAD: %s" % unknown[0])
    return sorted(shas, key=lambda s: rank[s])


# ---------------------------------------------------------------------------
# build / verify / drop  (F17, R2, F12, FL-01)
# ---------------------------------------------------------------------------

def _assert_clean(repo):
    proc = _git(repo, "status", "--porcelain", "--", PLUGIN_SUBDIR)
    if proc.returncode != 0:
        raise BatchError("git status failed: %s" % proc.stdout.strip())
    if proc.stdout.strip():
        raise BatchError("working tree not clean under %s — a dirty tree means the "
                         "batch is not actually complete at that commit"
                         % PLUGIN_SUBDIR)


def _assert_archive_tree(repo, commit, expected):
    """F12: the sealed Phase-38 baseline must be intact in anything the owner
    runs against. A TREE hash, not a commit."""
    proc = _git(repo, "rev-parse", "%s:%s" % (commit, ARCHIVE_PATH))
    actual = proc.stdout.strip() if proc.returncode == 0 else None
    if actual != expected:
        raise BatchError("sealed archive tree mismatch at %s: expected %s, found %s"
                         % (ARCHIVE_PATH, expected, actual or "<absent>"))


def _assert_completeness(plugin_root):
    """F17: every lazy-read target must EXIST in the snapshot.

    This is the 40-08/40-10 hazard: 40-08 replaces phase bodies with references to
    files only 40-10 creates, and commits in between. A snapshot built at such a
    commit exposes a plugin that cannot execute.
    """
    scanned = []
    for sub, pattern in (("commands", "*.md"), ("agents", "*.md"), ("phases", "*.md")):
        base = os.path.join(plugin_root, sub)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs.sort()
            for name in sorted(files):
                if name.endswith(".md"):
                    scanned.append(os.path.join(root, name))

    total = 0
    dangling = []
    for path in scanned:
        with open(path, errors="replace") as fh:
            text = fh.read()
        rel_src = os.path.relpath(path, plugin_root).replace(os.sep, "/")
        for target in read_targets(text):
            total += 1
            if not os.path.isfile(os.path.join(plugin_root, target)):
                dangling.append((rel_src, target))

    if dangling:
        lines = ["incomplete snapshot: %d dangling lazy-read target(s)" % len(dangling)]
        for src, target in dangling:
            lines.append("  %s references %s which does not exist in the snapshot"
                         % (src, target))
        raise BatchError("\n".join(lines))

    # A snapshot with a phases/ dir but ZERO read instructions is exactly the
    # broken state this check exists to catch, and a silently-zero regex would
    # report success on it.
    if os.path.isdir(os.path.join(plugin_root, "phases")) and total == 0:
        raise BatchError("incomplete snapshot: the plugin has a phases/ directory but "
                         "zero lazy-read instructions reference it — the spine cannot "
                         "load its sub-files")
    return total


def _pytest_argv():
    """How to invoke pytest, in preference order.

    The project's runner is the bare `pytest` executable from the scripts dir —
    NOT `<interpreter> -m pytest`. Those are different interpreters here: pytest
    is installed in its own pipx venv, so `sys.executable -m pytest` fails with
    "No module named pytest" under the very python the owner types
    (`python3 batchsnap.py build`). Preferring sys.executable would make `build`
    refuse EVERY valid batch with a bogus "suite is not green".
    """
    return [["pytest", "-q"], [sys.executable, "-m", "pytest", "-q"]]


def _assert_suite_green(plugin_root):
    scripts = os.path.join(plugin_root, "scripts")
    if not os.path.isdir(scripts):
        raise BatchError("snapshot has no scripts/ directory to test")
    attempts = []
    for argv in _pytest_argv():
        try:
            proc = subprocess.run(argv, cwd=scripts, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, timeout=120)
        except OSError as exc:
            attempts.append("%s: %s" % (argv[0], exc))
            continue
        out = proc.stdout.strip()
        # "no pytest here" is NOT a red suite -- fall through to the next runner
        # rather than reporting a green batch as broken.
        if proc.returncode != 0 and "No module named pytest" in out:
            attempts.append("%s: no pytest in that interpreter" % " ".join(argv[:2]))
            continue
        if proc.returncode != 0:
            tail = "\n".join(out.splitlines()[-5:])
            raise BatchError("suite is not green in the snapshot (pytest exit %d):\n%s"
                             % (proc.returncode, tail))
        return out.splitlines()[-1] if out else "green"
    raise BatchError("cannot run the suite in the snapshot — no usable pytest:\n  %s"
                     % "\n  ".join(attempts))


def build(repo, batch, commit, recorded, snap_root=None, archive_tree=None):
    """Build an immutable snapshot at `commit`. Returns the manifest dict.

    Order matters and is FL-01's correction: every validation that can mutate the
    tree runs BEFORE anything is hashed or sealed.

      1. working tree clean under plugins/vibe-check
      2. worktree add --detach  -> snapshot_root
      2b. plugin_root/.claude-plugin/plugin.json exists (R2)
      3. sealed archive tree matches the pin (F12)
      4. completeness: every lazy-read target exists (F17)
      5. suite green IN THE SNAPSHOT  <- writes __pycache__ into the tree
      6. resolve the batch commit set (F18)
      7. hash          <- first read of the final tree state
      8. write MANIFEST.json
      9. chmod -R a-w  <- seal, the LAST action
    """
    snap_root = snap_root or SNAP_ROOT
    repo = os.path.abspath(repo)

    _assert_clean(repo)

    full = _git(repo, "rev-parse", "--verify", "%s^{commit}" % commit)
    if full.returncode != 0:
        raise BatchError("commit does not exist in this repo")
    commit = full.stdout.strip()

    snapshot_root = os.path.join(os.path.expanduser(snap_root),
                                 "batch%d-%s" % (batch, commit[:12]))
    plugin_root = plugin_root_of(snapshot_root)

    if os.path.exists(snapshot_root):
        raise BatchError("snapshot already exists: %s — drop it first "
                         "(batchsnap.py drop --snap %s)" % (snapshot_root, snapshot_root))
    os.makedirs(os.path.dirname(snapshot_root), exist_ok=True)

    proc = _git(repo, "worktree", "add", "--detach", snapshot_root, commit)
    if proc.returncode != 0:
        raise BatchError("git worktree add failed: %s" % proc.stdout.strip())

    try:
        # (2b) R2: refuse if the plugin manifest is not where --plugin-dir will
        # look for it. This is what makes the two-root distinction mechanical.
        if not os.path.isfile(os.path.join(plugin_root, ".claude-plugin", "plugin.json")):
            raise BatchError(
                "refusing to build: %s/.claude-plugin/plugin.json is missing — "
                "claude --plugin-dir would load NO plugin and the run would "
                "silently measure the installed cache instead of this batch"
                % PLUGIN_SUBDIR)

        _assert_archive_tree(repo, commit, archive_tree or ARCHIVE_TREE)
        reads = _assert_completeness(plugin_root)
        suite = _assert_suite_green(plugin_root)
        batch_commits = commit_set(repo, batch, recorded)

        # --- sealing begins; nothing above may run after this point (FL-01) ---
        files = {rel: _sha256(os.path.join(plugin_root, rel))
                 for rel in _walk_files(plugin_root)}
        manifest = {
            "batch": batch,
            "snapshot_commit": commit,
            "snapshot_root": snapshot_root,
            "plugin_root": plugin_root,
            "built_at": _git_out(repo, "log", "-1", "--format=%cI", commit),
            "files": files,
            "commit_set": batch_commits,
            "suite_green": suite,
            "archive_tree": archive_tree or ARCHIVE_TREE,
            "hash_exclude": list(HASH_EXCLUDE),
            "read_instructions": reads,
        }
        with open(os.path.join(snapshot_root, MANIFEST_NAME), "w") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
            fh.write("\n")
        _chmod_ro(snapshot_root, plugin_root)
    except BaseException:
        # A half-built snapshot must not be left where a reader could launch
        # against it, and must not linger as a worktree registration.
        drop(snapshot_root, repo=repo, quiet=True)
        raise

    return manifest


def verify(snap):
    """Re-hash a snapshot against its manifest. Exit-code semantics: 0/1/2.

    The owner runs this before EVERY run, so a snapshot that changed under them is
    caught (F17 provenance). On success the LAST line printed is
    `plugin_root: <path>` — the launch argument, taken from a just-verified
    snapshot rather than retyped (R2).
    """
    snapshot_root = normalize_snap(snap)
    if snapshot_root is None:
        sys.stderr.write("usage error: %s is neither a snapshot root nor a plugin "
                         "root with a %s\n" % (snap, MANIFEST_NAME))
        return 2
    try:
        with open(os.path.join(snapshot_root, MANIFEST_NAME)) as fh:
            manifest = json.load(fh)
    except (ValueError, OSError) as exc:
        sys.stderr.write("usage error: unreadable manifest: %s\n" % exc)
        return 2

    plugin_root = plugin_root_of(snapshot_root)
    exclude = manifest.get("hash_exclude", HASH_EXCLUDE)
    reasons = []

    if not os.path.isfile(os.path.join(plugin_root, ".claude-plugin", "plugin.json")):
        reasons.append("plugin manifest missing: %s/.claude-plugin/plugin.json"
                       % PLUGIN_SUBDIR)

    recorded = manifest.get("files", {})
    present = _walk_files(plugin_root, exclude)
    for rel in present:
        full = os.path.join(plugin_root, rel)
        if rel not in recorded:
            reasons.append("file not in manifest: %s" % rel)
            continue
        if _sha256(full) != recorded[rel]:
            reasons.append("sha256 mismatch: %s" % rel)
    for rel in sorted(recorded):
        if rel not in present:
            reasons.append("file missing from snapshot: %s" % rel)

    # The seal itself: a writable snapshot is not a snapshot, even if every byte
    # still matches.
    writable = []
    for root, dirs, files in os.walk(snapshot_root):
        for name in files:
            p = os.path.join(root, name)
            if os.path.islink(p):
                continue
            rel = os.path.relpath(p, plugin_root).replace(os.sep, "/")
            if rel.startswith("..") or is_excluded(rel, exclude):
                continue
            if os.access(p, os.W_OK):
                writable.append(rel)
    for rel in sorted(writable)[:20]:
        reasons.append("snapshot is writable: %s" % rel)

    if reasons:
        for reason in reasons:
            sys.stdout.write(reason + "\n")
        return 1
    sys.stdout.write("snapshot verified: %d files\n" % len(recorded))
    sys.stdout.write("plugin_root: %s\n" % plugin_root)
    return 0


def drop(snap, repo=None, quiet=False):
    """Remove a snapshot: relax the seal, then deregister the worktree."""
    snapshot_root = normalize_snap(snap) or os.path.abspath(os.path.expanduser(snap))
    if not os.path.exists(snapshot_root):
        return 0
    try:
        _chmod_rw(snapshot_root)
    except OSError:
        pass
    repo = repo or os.path.dirname(snapshot_root)
    proc = _git(repo, "worktree", "remove", "--force", snapshot_root)
    if proc.returncode != 0 and os.path.exists(snapshot_root):
        if not quiet:
            sys.stderr.write("worktree remove failed: %s\n" % proc.stdout.strip())
        return 1
    _git(repo, "worktree", "prune")
    return 0


# ---------------------------------------------------------------------------
# check-pass  (F10, FL-02)
# ---------------------------------------------------------------------------

def check_pass_artifact(path, expect_commit=None, schema=None):
    """Validate an owner PASS artifact. Returns (ok, reasons) — the FULL list.

    FL-02 (R8): a PASS verdict is not certifiable from key presence. Beyond the
    required keys and enums this additionally requires successful mechanical
    VALUES, unique (diff, run_index) identities, both captured artifacts existing
    on disk, and non-failing trace validation. An artifact whose every key is
    present, whose verdict says PASS, and whose runs recorded `state_shape: FAIL`
    / `tree_diff_sha_match: false` is REJECTED — that combination is a schema
    violation, not a pass.
    """
    schema = schema or load_schema()
    reasons = []

    if not os.path.isfile(path):
        return False, ["PASS artifact not found: %s" % path]
    try:
        with open(path) as fh:
            art = json.load(fh)
    except ValueError as exc:
        return False, ["PASS artifact is not valid JSON: %s" % exc]
    if not isinstance(art, dict):
        return False, ["PASS artifact is not an object"]

    # realpath BOTH sides: on macOS /var is a symlink to /private/var, so
    # comparing a realpath'd candidate against a merely-absolute base would
    # refuse every legitimate artifact under a tmp dir.
    base = os.path.realpath(os.path.dirname(os.path.abspath(path)))

    for key in schema["pass_artifact_required"]:
        if key not in art:
            reasons.append("missing required key: %s" % key)

    verdict = art.get("verdict")
    if "verdict" in art:
        if verdict not in schema["verdict_enum"]:
            reasons.append("verdict not in enum: %s" % verdict)
        elif verdict == "FAIL":
            reasons.append("verdict is FAIL")

    if expect_commit is not None and art.get("snapshot_commit") != expect_commit:
        reasons.append("snapshot_commit does not match the batch manifest")

    runs = art.get("runs")
    if not isinstance(runs, list):
        reasons.append("runs is not a list")
        return False, reasons

    need = schema.get("runs_required_per_batch", 2)
    if len(runs) < need:
        reasons.append("too few runs: %d recorded, batch requires %d"
                       % (len(runs), need))

    seen = set()
    for i, run in enumerate(runs):
        tag = "run %d" % i
        if not isinstance(run, dict):
            reasons.append("%s is not an object" % tag)
            continue
        for key in schema["run_required"]:
            if key not in run:
                reasons.append("missing required key in run: %s (%s)" % (key, tag))

        # (1) successful mechanical VALUES, not merely present keys.
        if "state_shape" in run:
            if run["state_shape"] not in schema["state_shape_enum"]:
                reasons.append("state_shape not in enum: %r (%s)"
                               % (run["state_shape"], tag))
            elif run["state_shape"] != schema["state_shape_success"]:
                reasons.append("state_shape recorded a failure: %s (%s)"
                               % (run["state_shape"], tag))
        if "tree_diff_sha_match" in run:
            value = run["tree_diff_sha_match"]
            if not isinstance(value, bool):
                reasons.append("tree_diff_sha_match is not a boolean: %r (%s)"
                               % (value, tag))
            elif value is not schema["tree_diff_sha_match_success"]:
                reasons.append("tree_diff_sha_match recorded a failure (%s)" % tag)

        # (4) trace validation.
        if "trace_validation" in run:
            tv = run["trace_validation"]
            if tv not in schema["trace_validation_enum"]:
                reasons.append("trace_validation not in enum: %r (%s)" % (tv, tag))
            elif tv == schema["trace_validation_failure"]:
                reasons.append("trace_validation recorded a failure (%s)" % tag)

        # adjudication: an unadjudicated run cannot carry a batch past a barrier.
        if "adjudication" in run:
            adj = run["adjudication"]
            if adj not in schema["adjudication_enum"]:
                reasons.append("adjudication not in enum: %r (%s)" % (adj, tag))
            elif adj == schema["adjudication_unresolved"]:
                reasons.append("adjudication is still %s (%s) — the assistant has not "
                               "adjudicated this run" % (adj, tag))

        # (2) unique run identity.
        identity = tuple(run.get(k) for k in schema["run_identity_keys"])
        if all(v is not None for v in identity):
            if identity in seen:
                reasons.append("duplicate run identity: %r (%s)" % (identity, tag))
            seen.add(identity)

        # (3) the two captured artifacts must EXIST, inside the artifact's dir.
        for key in schema["run_artifact_keys"]:
            rel = run.get(key)
            if not isinstance(rel, str) or not rel.strip():
                if key in run:
                    reasons.append("%s is not a path (%s)" % (key, tag))
                continue
            target = os.path.realpath(os.path.join(base, rel))
            if target != base and not target.startswith(base + os.sep):
                reasons.append("%s resolves outside the artifact directory (%s)"
                               % (key, tag))
            elif not os.path.isfile(target):
                reasons.append("%s does not exist: %s (%s)" % (key, rel, tag))

    return (not reasons), reasons


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run(argv):
    parser = argparse.ArgumentParser(
        prog="batchsnap.py", description="Batch lifecycle (see module docstring).")
    sub = parser.add_subparsers(dest="cmd")

    p_build = sub.add_parser("build")
    p_build.add_argument("--batch", type=int, required=True)
    p_build.add_argument("--commit", required=True)
    p_build.add_argument("--recorded", required=True)
    p_build.add_argument("--repo", default=".")
    p_build.add_argument("--snap-root", default=None)
    p_build.add_argument("--archive-tree", default=None)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--snap", required=True)

    p_cs = sub.add_parser("commit-set")
    p_cs.add_argument("--batch", type=int, required=True)
    p_cs.add_argument("--recorded", required=True)
    p_cs.add_argument("--repo", default=".")

    p_rc = sub.add_parser("record-commit")
    p_rc.add_argument("--plan", required=True)
    p_rc.add_argument("--sha", required=True)
    p_rc.add_argument("--recorded", required=True)
    p_rc.add_argument("--repo", default=".")

    p_cp = sub.add_parser("check-pass")
    p_cp.add_argument("--file", required=True)
    p_cp.add_argument("--expect-commit", default=None)

    p_drop = sub.add_parser("drop")
    p_drop.add_argument("--snap", required=True)
    p_drop.add_argument("--repo", default=None)

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2

    try:
        if args.cmd == "build":
            manifest = build(args.repo, args.batch, args.commit, args.recorded,
                             snap_root=args.snap_root, archive_tree=args.archive_tree)
            sys.stdout.write("batch: %d\n" % manifest["batch"])
            sys.stdout.write("snapshot_commit: %s\n" % manifest["snapshot_commit"])
            for sha in manifest["commit_set"]:
                sys.stdout.write("commit_set: %s\n" % sha)
            # Both roots, labelled. 40-09's checklist and 40-13's capture quote
            # these labels; a reader who copies the wrong line gets a run against
            # the installed cache rather than the batch (R2).
            sys.stdout.write("snapshot_root: %s\n" % manifest["snapshot_root"])
            sys.stdout.write("plugin_root: %s\n" % manifest["plugin_root"])
            return 0

        if args.cmd == "verify":
            return verify(args.snap)

        if args.cmd == "commit-set":
            for sha in commit_set(args.repo, args.batch, args.recorded):
                sys.stdout.write(sha + "\n")
            return 0

        if args.cmd == "record-commit":
            return record_commit(args.repo, args.plan, args.sha, args.recorded)

        if args.cmd == "check-pass":
            ok, reasons = check_pass_artifact(args.file, expect_commit=args.expect_commit)
            for reason in reasons:
                sys.stdout.write(reason + "\n")
            if ok:
                sys.stdout.write("PASS artifact valid\n")
            return 0 if ok else 1

        if args.cmd == "drop":
            return drop(args.snap, repo=args.repo)
    except BatchError as exc:
        sys.stdout.write(str(exc) + "\n")
        return 1

    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
