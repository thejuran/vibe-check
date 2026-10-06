"""test_batchsnap.py — the batch lifecycle mechanism (40-06).

D-06 says restructure batches are independently revertable and DIET-04 says each
batch is validated before the next lands. Before this module both were prose. The
tests here lock the three properties that make them mechanical:

* **No owner run ever observes a mid-construction plugin (F17).** Runs target an
  immutable `git worktree` snapshot, not the working tree. `build` refuses a dirty
  tree, refuses a snapshot with a dangling lazy-read target, and `verify` re-hashes
  every file before each run so a snapshot that drifted is caught.
* **The rollback unit is an ALLOWLIST over recorded identities, never a subject
  filter (F18, R3).** `BATCH_PLANS` names plan ids; `PLAN-COMMITS.json` maps plan
  ids to shas each plan recorded for itself. `commit_set` asserts `NEVER_REVERT`
  from the inside, so a typo in the allowlist fails the command rather than
  silently reverting evidence.
* **Advancement consumes evidence (F10).** `check_pass_artifact` validates the
  owner's PASS artifact; a barrier task runs it and halts on absence, malformation,
  or FAIL.

Defects these tests lock:

* R2 — `snapshot_root` and `plugin_root` are DIFFERENT paths. A snapshot worktree
  is a full-repo checkout and the plugin lives at `plugins/vibe-check`, so
  `--plugin-dir "$SNAP_ROOT"` loads NO plugin and every run would silently exercise
  the installed cache instead of the batch under test. `build` refuses a snapshot
  lacking `plugin_root/.claude-plugin/plugin.json`; `verify` prints `plugin_root:`
  as its LAST line so the launch argument comes from a just-verified snapshot.
* R3 — the previous selector was "plugin-touching commits in a range, minus
  subjects tagged `(40-01)`". 40-01's real subject carries no plan tag AND it
  touches `plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md`, so that selector
  would have swept the append-only SUPERSESSIONS ledger commit into the revert set.
  `test_commit_set_excludes_40_01_by_identity_not_subject` reproduces exactly that
  commit — real subject, real touched path — and asserts it is excluded.
* F12 — the sealed-baseline assertion pins the archive TREE
  `82c412b6e58b5d5a1dbddca0239f0f4b26833b4a`, not the commit `633f1dd` which
  predates the archives entirely and would have failed on valid evidence.

Fix-list corrections locked here:

* FL-01 (R5) — sealing is the LAST action in `build`: completeness, then the suite,
  then `commit_set`, then hash, then MANIFEST, then `chmod -R a-w`. Nothing is
  hashed until every tree-mutating validation has finished. Generated files live in
  the `HASH_EXCLUDE` module constant, which is RECORDED INSIDE the manifest so
  `verify` uses the list the build used rather than a constant that may have
  drifted. `test_verify_survives_cache_churn` regenerates caches in a SEPARATE
  writable copy and copies only the excluded paths back, because `verify` asserts
  the tree is still read-only and `chmod u+w`-ing the sealed tree would fail that
  assertion instead of exercising the exclusion (A4).
* FL-02 (R8) — a PASS verdict is not certifiable from key presence. The schema and
  `check_pass_artifact` additionally require successful mechanical VALUES, unique
  `(diff, run_index)` identities, both captured artifacts existing on disk, and
  non-failing trace validation. `test_pass_rejects_pass_verdict_with_failed_*`
  are the direct reproductions: an artifact whose every key is present and whose
  verdict says PASS is REJECTED when the mechanical fields recorded failures.

A3 — 40-06 is itself in `NEVER_REVERT`, so this plan does not record its own commits
into `PLAN-COMMITS.json`; `test_never_revert_membership` locks the set.
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batchsnap  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BATCHSNAP_PY = os.path.join(HERE, "batchsnap.py")
SCHEMA_PATH = os.path.join(HERE, "fixtures", "batch-manifest-schema.json")

with open(SCHEMA_PATH) as _fh:
    SCHEMA = json.load(_fh)

# The real archive tree pin (F12). A tree hash, not a commit: stable under rebase.
ARCHIVE_TREE = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a"

# The REAL subject 40-01's ledger commit carries (40-01-PLAN.md). It has NO plan
# tag and it touches a file under plugins/vibe-check/ -- which is precisely why a
# subject-or-path heuristic would have swept it into batch 1's revert set.
LEDGER_SUBJECT = ("docs(b3): SUPERSESSIONS-v2.10 ledger (entries 001-004) + one pointer "
                  "line each in SCORING/RESULTS/RUN-METHOD-NOTES")
LEDGER_PATH = "plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md"


def git(repo, *args, **kw):
    """Run git in `repo`, raising on failure unless check=False."""
    check = kw.pop("check", True)
    proc = subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "-c", "commit.gpgsign=false", *args],
        cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=60)
    if check and proc.returncode != 0:
        raise AssertionError("git %s failed in %s:\n%s" % (args[0], repo, proc.stdout))
    return proc


def write(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


# A plugin scripts tree whose pytest run is fast and green -- build asserts the
# suite is green IN THE SNAPSHOT, so the fixture repo needs a real (tiny) suite.
TINY_TEST = """def test_ok():
    assert True
"""


def make_repo(tmp, with_plugin=True, with_phases=True, read_target_exists=True,
              archive_tree=True):
    """A tmp git repo shaped like the real one: plugin at plugins/vibe-check.

    `with_plugin=False` omits .claude-plugin/plugin.json so build must refuse (R2).
    `read_target_exists=False` leaves a dangling lazy-read target so build must
    refuse (F17). `with_phases=False` omits the phases/ dir entirely, which is the
    legitimate pre-40-08 shape.
    """
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    git(repo, "init", "-q", "-b", "main")
    plug = os.path.join(repo, "plugins", "vibe-check")
    if with_plugin:
        write(os.path.join(plug, ".claude-plugin", "plugin.json"),
              '{"name": "vibe-check", "version": "2.10.0"}\n')
    write(os.path.join(plug, "scripts", "test_tiny.py"), TINY_TEST)
    write(os.path.join(plug, "agents", "fix.md"), "# fix agent\n")
    if with_phases:
        # The lazy-read instruction form 40-08 establishes: a Read followed by
        # either the ${CLAUDE_PLUGIN_ROOT}/ token (head paths, loader-processed)
        # or the resolved $VC_ROOT/ value (nested reads).
        write(os.path.join(plug, "commands", "review.md"),
              "# review\n\n"
              "**Read ${CLAUDE_PLUGIN_ROOT}/phases/shared/00-contract.md before anything.**\n\n"
              "Then Read $VC_ROOT/phases/review/00-scope.md\n")
        write(os.path.join(plug, "phases", "shared", "00-contract.md"), "# contract\n")
        if read_target_exists:
            write(os.path.join(plug, "phases", "review", "00-scope.md"), "# scope\n")
    else:
        write(os.path.join(plug, "commands", "review.md"), "# review\n\nno sub-files yet\n")
    if archive_tree:
        # A stand-in sealed archive; the pin is computed from THIS tree so the
        # fixture exercises the comparison rather than hard-coding a match.
        write(os.path.join(repo, "docs", "design", "b3-ground-truth",
                           "runs-v2.10", "sealed.txt"), "sealed evidence\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def repo_archive_tree(repo, rev="HEAD"):
    proc = git(repo, "rev-parse", "%s:docs/design/b3-ground-truth/runs-v2.10" % rev,
               check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def make_commit(repo, plan_id, subject=None, path=None):
    """One commit attributable to `plan_id`; returns its full sha."""
    rel = path or "plugins/vibe-check/docs/%s.md" % plan_id
    p = os.path.join(repo, rel)
    prev = ""
    if os.path.exists(p):
        with open(p) as fh:
            prev = fh.read()
    write(p, prev + "change for %s\n" % plan_id)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject or "feat(%s): work" % plan_id)
    return head(repo)


def make_run(**over):
    """A fully-successful run record; pass a key to override, DROP to remove."""
    run = {
        "diff": "should-catch-3",
        "run_index": 1,
        "state_shape": "PASS",
        "tree_diff_sha_match": True,
        "adjudication": "catch",
        "report_path": "run1/report.md",
        "transcript_path": "run1/transcript.jsonl",
        "trace_validation": "not-applicable",
    }
    run.update(over)
    return {k: v for k, v in run.items() if v is not DROP}


def make_pass(**over):
    """A well-formed PASS artifact with the 2 runs a batch requires."""
    art = {
        "batch": 1,
        "snapshot_commit": "a" * 40,
        "verdict": "PASS",
        "runs": [make_run(diff="should-catch-3", run_index=1,
                          report_path="run1/report.md",
                          transcript_path="run1/transcript.jsonl"),
                 make_run(diff="should-quiet-2", run_index=1, adjudication="clean",
                          report_path="run2/report.md",
                          transcript_path="run2/transcript.jsonl")],
        "recorded_by": "owner",
        "recorded_at": "2026-09-08T12:00:00Z",
    }
    art.update(over)
    return {k: v for k, v in art.items() if v is not DROP}


class _Drop(object):
    def __repr__(self):
        return "DROP"


DROP = _Drop()


def write_pass(tmpdir, artifact, make_artifacts=True):
    """Write a PASS artifact plus (by default) the captured run files it names."""
    path = os.path.join(tmpdir, "PASS.json")
    write(path, json.dumps(artifact, indent=2))
    if make_artifacts:
        for run in artifact.get("runs", []):
            if not isinstance(run, dict):
                continue
            for key in SCHEMA["run_artifact_keys"]:
                rel = run.get(key)
                if isinstance(rel, str):
                    write(os.path.join(tmpdir, rel), "captured\n")
    return path


class SnapCase(unittest.TestCase):
    """Base: a tmp repo + an isolated SNAP_ROOT, with every snapshot dropped."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.snaproot = os.path.join(self.tmp, "snaps")
        self._made = []

    def tearDown(self):
        for repo, snap in self._made:
            batchsnap.drop(snap, repo=repo)
        self._tmp.cleanup()

    def build(self, repo, batch=1, commit=None, recorded=None, expect=0,
              archive_tree=None):
        """Run build as a SUBPROCESS (the owner's interface) and return (proc, snap)."""
        commit = commit or head(repo)
        if recorded is None:
            recorded = self.record_all(repo, batch)
        argv = [sys.executable, BATCHSNAP_PY, "build", "--batch", str(batch),
                "--commit", commit, "--recorded", recorded,
                "--repo", repo, "--snap-root", self.snaproot,
                "--archive-tree", archive_tree or repo_archive_tree(repo, commit) or "none"]
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=300)
        snap = self.snap_path(batch, commit)
        if proc.returncode == 0:
            self._made.append((repo, snap))
        self.assertEqual(proc.returncode, expect,
                         "build exit %d (wanted %d):\n%s"
                         % (proc.returncode, expect, proc.stdout))
        return proc, snap

    def snap_path(self, batch, commit):
        return os.path.join(self.snaproot, "batch%d-%s" % (batch, commit[:12]))

    def record_all(self, repo, batch, skip=(), extra_plans=()):
        """Record one commit per member of BATCH_PLANS[batch]; return the file path."""
        recorded = os.path.join(self.tmp, "PLAN-COMMITS-%d.json" % batch)
        for plan in batchsnap.BATCH_PLANS[batch]:
            if plan in skip:
                continue
            sha = make_commit(repo, plan)
            self.assertEqual(batchsnap.record_commit(repo, plan, sha, recorded), 0)
        for plan in extra_plans:
            sha = make_commit(repo, plan)
            self.assertEqual(batchsnap.record_commit(repo, plan, sha, recorded), 0)
        return recorded

    def verify(self, snap):
        proc = subprocess.run([sys.executable, BATCHSNAP_PY, "verify", "--snap", snap],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=120)
        return proc


# --------------------------------------------------------------------------
# R2 — the two roots
# --------------------------------------------------------------------------

class TestTwoRoots(SnapCase):
    """R2: snapshot_root != plugin_root, and only plugin_root is launchable."""

    def test_plugin_root_is_nested_under_snapshot_root(self):
        repo = make_repo(self.tmp)
        proc, snap = self.build(repo)
        with open(os.path.join(snap, "MANIFEST.json")) as fh:
            man = json.load(fh)
        self.assertIn("snapshot_root", man)
        self.assertIn("plugin_root", man)
        self.assertNotEqual(man["snapshot_root"], man["plugin_root"])
        self.assertEqual(man["plugin_root"],
                         man["snapshot_root"] + "/" + batchsnap.PLUGIN_SUBDIR)
        self.assertTrue(man["plugin_root"].endswith("/plugins/vibe-check"))
        # The launch argument is where the plugin manifest actually is -- and the
        # snapshot root is NOT (passing it to --plugin-dir loads no plugin at all).
        self.assertTrue(os.path.isfile(
            os.path.join(man["plugin_root"], ".claude-plugin", "plugin.json")))
        self.assertFalse(os.path.exists(
            os.path.join(man["snapshot_root"], ".claude-plugin", "plugin.json")))

    def test_build_prints_both_roots_labelled(self):
        repo = make_repo(self.tmp)
        proc, snap = self.build(repo)
        lines = proc.stdout.splitlines()
        snap_lines = [l for l in lines if l.startswith("snapshot_root: ")]
        plug_lines = [l for l in lines if l.startswith("plugin_root: ")]
        self.assertEqual(len(snap_lines), 1, proc.stdout)
        self.assertEqual(len(plug_lines), 1, proc.stdout)
        # 40-09's checklist and 40-13's capture QUOTE these labels; a reader who
        # copies the wrong line measures the installed cache instead of the batch.
        self.assertEqual(snap_lines[0], "snapshot_root: " + snap)
        self.assertEqual(plug_lines[0],
                         "plugin_root: " + os.path.join(snap, batchsnap.PLUGIN_SUBDIR))

    def test_build_refuses_missing_plugin_manifest(self):
        repo = make_repo(self.tmp, with_plugin=False)
        proc, _ = self.build(repo, expect=1)
        self.assertIn(".claude-plugin/plugin.json", proc.stdout)
        # And it left no half-built snapshot registered behind it.
        self.assertEqual(
            git(repo, "worktree", "list").stdout.count(self.snaproot), 0, proc.stdout)

    def test_verify_prints_plugin_root_as_last_line(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        proc = self.verify(snap)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        last = proc.stdout.strip().splitlines()[-1]
        self.assertEqual(last, "plugin_root: " + os.path.join(snap, batchsnap.PLUGIN_SUBDIR))

    def test_verify_accepts_either_root_and_normalizes(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        as_snap = self.verify(snap)
        as_plug = self.verify(os.path.join(snap, batchsnap.PLUGIN_SUBDIR))
        self.assertEqual(as_snap.returncode, 0, as_snap.stdout)
        self.assertEqual(as_plug.returncode, 0, as_plug.stdout)
        self.assertEqual(as_snap.stdout, as_plug.stdout)

    def test_verify_rejects_unrelated_path_as_usage_error(self):
        proc = self.verify(os.path.join(self.tmp, "nowhere"))
        self.assertEqual(proc.returncode, 2, proc.stdout)


# --------------------------------------------------------------------------
# F17 — immutability and completeness
# --------------------------------------------------------------------------

class TestSnapshotImmutable(SnapCase):

    def test_snapshot_is_immutable(self):
        """Every file carrying an integrity claim is read-only after build.

        Generated files are deliberately NOT sealed (FL-01): they carry no
        integrity claim, and sealing them would turn any legitimate run inside the
        snapshot into a permission error. test_generated_paths_stay_writable is
        the twin that pins that exemption so it cannot silently widen.
        """
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        plug = os.path.join(snap, batchsnap.PLUGIN_SUBDIR)
        writable = []
        seen = 0
        for root, _dirs, files in os.walk(snap):
            for f in files:
                p = os.path.join(root, f)
                if os.path.islink(p):
                    continue
                rel = os.path.relpath(p, plug).replace(os.sep, "/")
                if not rel.startswith("..") and batchsnap.is_excluded(rel):
                    continue
                seen += 1
                if os.access(p, os.W_OK):
                    writable.append(rel)
        # Fixture integrity: the walk actually saw the tree it claims to judge.
        self.assertGreater(seen, 3, "walk found almost nothing -- fixture is vacuous")
        self.assertEqual(writable, [])
        self.assertEqual(self.verify(snap).returncode, 0)

    def test_generated_paths_stay_writable(self):
        """FL-01: the exemption is exactly HASH_EXCLUDE, and no wider.

        build runs pytest in the snapshot, so the caches exist before sealing.
        They stay writable; every sibling under the same directory does not.
        """
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        plug = os.path.join(snap, batchsnap.PLUGIN_SUBDIR)
        excluded = []
        for root, _dirs, files in os.walk(snap):
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, plug).replace(os.sep, "/")
                if not rel.startswith("..") and batchsnap.is_excluded(rel):
                    excluded.append((rel, os.access(p, os.W_OK)))
        # Fixture integrity: build's own pytest run really did generate caches.
        self.assertTrue(excluded, "no generated files -- exemption test is vacuous")
        self.assertEqual([r for r, w in excluded if not w], [],
                         "a sealed cache file would break any run in the snapshot")
        # The exemption did NOT widen to the containing directory's real files.
        self.assertFalse(os.access(os.path.join(plug, "scripts", "test_tiny.py"),
                                   os.W_OK))

    def test_sealed_dirs_stay_traversable(self):
        # chmod -R a-w must clear write bits ONLY; stripping x makes the tree
        # untraversable and verify could never re-hash it.
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        plug = os.path.join(snap, batchsnap.PLUGIN_SUBDIR)
        self.assertTrue(os.access(plug, os.X_OK))
        self.assertTrue(os.access(plug, os.R_OK))
        self.assertTrue(os.path.isfile(os.path.join(plug, "agents", "fix.md")))

    def test_verify_detects_modified_file(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        target = os.path.join(snap, batchsnap.PLUGIN_SUBDIR, "agents", "fix.md")
        os.chmod(target, 0o644)
        with open(target, "a") as fh:
            fh.write("tampered\n")
        # FL-01/A4: the negative twin necessarily relaxes permissions, so it must
        # restore a-w before calling verify -- otherwise it would trip the
        # read-only assertion instead of the hash comparison it exists to test.
        os.chmod(target, 0o444)
        proc = self.verify(snap)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("agents/fix.md", proc.stdout)

    def test_verify_detects_added_file(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        plug = os.path.join(snap, batchsnap.PLUGIN_SUBDIR)
        os.chmod(plug, 0o755)
        write(os.path.join(plug, "smuggled.md"), "extra\n")
        os.chmod(os.path.join(plug, "smuggled.md"), 0o444)
        os.chmod(plug, 0o555)
        proc = self.verify(snap)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("smuggled.md", proc.stdout)

    def test_verify_detects_writable_tree(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        target = os.path.join(snap, batchsnap.PLUGIN_SUBDIR, "agents", "fix.md")
        os.chmod(target, 0o644)  # content unchanged; only the seal is broken
        proc = self.verify(snap)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("writable", proc.stdout.lower())

    def test_verify_survives_cache_churn(self):
        """FL-01: pytest's __pycache__ is not tampering.

        The churn is created in a SEPARATE writable copy and only the excluded
        paths are copied back (A4): verify asserts the tree is still read-only, so
        chmod u+w-ing the sealed tree would fail the very assertion this test is
        not trying to exercise.
        """
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        self.assertEqual(self.verify(snap).returncode, 0)

        work = os.path.join(self.tmp, "churn")
        shutil.copytree(snap, work)
        for root, dirs, files in os.walk(work):
            os.chmod(root, 0o755)
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        scripts = os.path.join(work, batchsnap.PLUGIN_SUBDIR, "scripts")
        subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=scripts,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=300)
        churned = []
        for root, _dirs, files in os.walk(work):
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, work)
                if batchsnap.is_excluded(rel):
                    churned.append(rel)
        # Fixture integrity: the churn actually happened. Without this the test
        # would "pass" by copying nothing back and proving nothing.
        self.assertTrue(any(r.endswith(".pyc") for r in churned),
                        "pytest produced no .pyc -- churn fixture is vacuous: %r" % churned)

        sealed_plug = os.path.join(snap, batchsnap.PLUGIN_SUBDIR)
        copied = 0
        for rel in churned:
            src = os.path.join(work, rel)
            dst = os.path.join(snap, rel)
            d = os.path.dirname(dst)
            if not os.path.isdir(d):
                # Create the cache DIRECTORY only; no sealed file is touched.
                parent = os.path.dirname(d)
                pmode = os.stat(parent).st_mode
                os.chmod(parent, 0o755)
                os.makedirs(d, exist_ok=True)
                os.chmod(parent, pmode)
            shutil.copyfile(src, dst)
            copied += 1
        self.assertGreater(copied, 0)
        # The sealed plugin files themselves are still read-only: the churn added
        # only excluded paths.
        self.assertFalse(os.access(
            os.path.join(sealed_plug, "agents", "fix.md"), os.W_OK))

        proc = self.verify(snap)
        self.assertEqual(proc.returncode, 0,
                         "cache churn must not read as tampering:\n%s" % proc.stdout)

    def test_hash_exclude_recorded_in_manifest(self):
        """FL-01: verify uses the list the BUILD used, not a drifted constant."""
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        with open(os.path.join(snap, "MANIFEST.json")) as fh:
            man = json.load(fh)
        self.assertEqual(list(man["hash_exclude"]), list(batchsnap.HASH_EXCLUDE))
        self.assertTrue(any("__pycache__" in p for p in man["hash_exclude"]))
        self.assertTrue(any(p.endswith(".pyc") for p in man["hash_exclude"]))
        self.assertTrue(any(".pytest_cache" in p for p in man["hash_exclude"]))
        self.assertEqual([f for f in man["files"] if batchsnap.is_excluded(f)], [])

    def test_verify_consumes_the_manifest_exclusion_list_not_the_constant(self):
        """FL-01: recording the list is not enough -- verify must USE it.

        A build's manifest is judged by the rules THAT BUILD used. Here the
        manifest records an exclusion the module constant does not carry: verify
        must honour the recorded one. If verify read HASH_EXCLUDE instead, the
        newly-excluded file would read as tampering and this exits 1.
        """
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        man_path = os.path.join(snap, "MANIFEST.json")
        with open(man_path) as fh:
            man = json.load(fh)
        # A real, hashed, non-excluded file under the module constant.
        victim = "agents/fix.md"
        self.assertIn(victim, man["files"])
        self.assertFalse(batchsnap.is_excluded(victim))

        man["hash_exclude"] = list(batchsnap.HASH_EXCLUDE) + ["fix.md"]
        del man["files"][victim]
        os.chmod(snap, 0o755)
        os.chmod(man_path, 0o644)
        write(man_path, json.dumps(man, indent=2, sort_keys=True))
        os.chmod(man_path, 0o444)
        os.chmod(snap, 0o555)

        proc = self.verify(snap)
        self.assertEqual(proc.returncode, 0,
                         "verify ignored the manifest's recorded hash_exclude and "
                         "fell back to the module constant:\n%s" % proc.stdout)
        # Fixture integrity: dropping the file from `files` WITHOUT the matching
        # exclusion really would be caught -- so the pass above came from the
        # recorded list, not from a verify that checks nothing.
        del man["hash_exclude"]
        os.chmod(snap, 0o755)
        os.chmod(man_path, 0o644)
        write(man_path, json.dumps(man, indent=2, sort_keys=True))
        os.chmod(man_path, 0o444)
        os.chmod(snap, 0o555)
        proc2 = self.verify(snap)
        self.assertEqual(proc2.returncode, 1, proc2.stdout)
        self.assertIn(victim, proc2.stdout)

    def test_manifest_paths_are_plugin_root_relative(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        with open(os.path.join(snap, "MANIFEST.json")) as fh:
            man = json.load(fh)
        self.assertIn("agents/fix.md", man["files"])
        self.assertFalse(any(p.startswith("/") or p.startswith("plugins/")
                             for p in man["files"]))
        self.assertEqual(len(man["files"][".claude-plugin/plugin.json"]), 64)

    def test_manifest_satisfies_schema_required_keys(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        with open(os.path.join(snap, "MANIFEST.json")) as fh:
            man = json.load(fh)
        for key in SCHEMA["manifest_required"]:
            self.assertIn(key, man)


class TestCompleteness(SnapCase):
    """F17: an incomplete batch cannot produce a valid snapshot."""

    def test_completeness_refuses_dangling_read(self):
        repo = make_repo(self.tmp, read_target_exists=False)
        proc, _ = self.build(repo, expect=1)
        # Names BOTH the referencing file and the missing target.
        self.assertIn("commands/review.md", proc.stdout)
        self.assertIn("phases/review/00-scope.md", proc.stdout)

    def test_completeness_passes_once_target_created(self):
        repo = make_repo(self.tmp, read_target_exists=False)
        self.build(repo, expect=1)
        write(os.path.join(repo, "plugins", "vibe-check", "phases", "review",
                           "00-scope.md"), "# scope\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "feat(40-10): add the missing sub-file")
        proc, snap = self.build(repo)
        self.assertTrue(os.path.isfile(os.path.join(snap, "MANIFEST.json")))

    def test_read_regex_matches_both_forms(self):
        """The token form (loader-processed heads) and the resolved $VC_ROOT form."""
        token = "**Read ${CLAUDE_PLUGIN_ROOT}/phases/shared/00-contract.md before anything.**"
        resolved = "Then Read $VC_ROOT/phases/review/00-scope.md"
        self.assertEqual(batchsnap.read_targets(token), ["phases/shared/00-contract.md"])
        self.assertEqual(batchsnap.read_targets(resolved), ["phases/review/00-scope.md"])
        self.assertEqual(batchsnap.read_targets("Read $VC_ROOT/scripts/guard.py"), [])
        self.assertEqual(batchsnap.read_targets("no read instruction here"), [])

    def test_phases_dir_with_zero_read_instructions_refuses(self):
        """A silently-zero regex would report success on exactly the broken state."""
        repo = make_repo(self.tmp)
        rm = os.path.join(repo, "plugins", "vibe-check", "commands", "review.md")
        write(rm, "# review\n\nthe spine forgot to say how to load its sub-files\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "break the read instructions")
        proc, _ = self.build(repo, expect=1)
        self.assertIn("zero", proc.stdout.lower())

    def test_no_phases_dir_is_legitimate(self):
        """The pre-40-08 shape: no phases/ dir, so no read instructions required."""
        repo = make_repo(self.tmp, with_phases=False)
        proc, snap = self.build(repo)
        self.assertTrue(os.path.isfile(os.path.join(snap, "MANIFEST.json")))

    def test_build_refuses_dirty_tree(self):
        repo = make_repo(self.tmp)
        recorded = self.record_all(repo, 1)
        write(os.path.join(repo, "plugins", "vibe-check", "agents", "fix.md"),
              "# fix agent\nuncommitted\n")
        proc, _ = self.build(repo, recorded=recorded, expect=1)
        self.assertIn("working tree not clean under plugins/vibe-check", proc.stdout)

    def test_build_refuses_red_suite(self):
        repo = make_repo(self.tmp)
        write(os.path.join(repo, "plugins", "vibe-check", "scripts", "test_tiny.py"),
              "def test_ok():\n    assert False\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "red")
        proc, _ = self.build(repo, expect=1)
        self.assertIn("suite", proc.stdout.lower())

    def test_build_works_under_the_interpreter_the_owner_types(self):
        """THE runner bug: `python3 batchsnap.py build` must not report a green
        batch as red.

        pytest lives in its own pipx venv here, so `sys.executable -m pytest`
        raises "No module named pytest" under the plain `python3` the lifecycle
        doc tells the owner to type. A build that resolved the runner as
        sys.executable would refuse EVERY valid batch with a bogus "suite is not
        green". This drives build through bare `python3` end to end.
        """
        repo = make_repo(self.tmp)
        recorded = self.record_all(repo, 1)
        commit = head(repo)
        proc = subprocess.run(
            ["python3", BATCHSNAP_PY, "build", "--batch", "1", "--commit", commit,
             "--recorded", recorded, "--repo", repo, "--snap-root", self.snaproot,
             "--archive-tree", repo_archive_tree(repo, commit)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
        snap = self.snap_path(1, commit)
        if proc.returncode == 0:
            self._made.append((repo, snap))
        self.assertEqual(proc.returncode, 0,
                         "build failed under bare python3:\n%s" % proc.stdout)
        self.assertNotIn("No module named pytest", proc.stdout)
        self.assertIn("plugin_root: ", proc.stdout)

    def test_missing_pytest_is_not_reported_as_a_red_suite(self):
        """The two failures are distinguishable: 'no runner' != 'suite is red'."""
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        plug = os.path.join(snap, batchsnap.PLUGIN_SUBDIR)
        real = batchsnap._pytest_argv
        try:
            batchsnap._pytest_argv = lambda: [[sys.executable, "-c",
                                               "import sys; sys.stdout.write("
                                               "'No module named pytest'); "
                                               "sys.exit(1)"]]
            with self.assertRaises(batchsnap.BatchError) as ctx:
                batchsnap._assert_suite_green(plug)
            msg = str(ctx.exception)
            self.assertIn("no usable pytest", msg)
            self.assertNotIn("suite is not green", msg)
        finally:
            batchsnap._pytest_argv = real

    def test_archive_tree_pinned(self):
        """F12: the sealed baseline must be intact in anything the owner runs against."""
        repo = make_repo(self.tmp)
        real = repo_archive_tree(repo)
        self.assertIsNotNone(real)
        # Matching pin -> builds.
        proc, snap = self.build(repo, archive_tree=real)
        with open(os.path.join(snap, "MANIFEST.json")) as fh:
            self.assertEqual(json.load(fh)["archive_tree"], real)
        # Wrong pin -> refuses, and names the mismatch.
        proc, _ = self.build(repo, archive_tree="0" * 40, expect=1)
        self.assertIn("archive", proc.stdout.lower())

    def test_archive_tree_pin_is_the_real_phase38_tree(self):
        """The pinned constant is the tree of the real sealed archives, not 633f1dd."""
        self.assertEqual(batchsnap.ARCHIVE_TREE, ARCHIVE_TREE)
        repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
        proc = git(repo_root, "rev-parse",
                   "HEAD:docs/design/b3-ground-truth/runs-v2.10", check=False)
        if proc.returncode == 0:
            self.assertEqual(proc.stdout.strip(), ARCHIVE_TREE)


class TestDrop(SnapCase):

    def test_drop_removes_worktree_registration(self):
        repo = make_repo(self.tmp)
        _, snap = self.build(repo)
        # Fixture integrity: the worktree really was registered, so the
        # post-drop absence assertion below is not vacuous.
        listed = git(repo, "worktree", "list").stdout
        self.assertTrue(snap in listed or os.path.realpath(snap) in listed,
                        "worktree not registered:\n%s" % listed)
        rc = batchsnap.drop(snap, repo=repo)
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(snap))
        self.assertNotIn(snap, git(repo, "worktree", "list").stdout)
        self._made = [(r, s) for r, s in self._made if s != snap]


# --------------------------------------------------------------------------
# F18 / R3 — the rollback unit
# --------------------------------------------------------------------------

class TestCommitSet(SnapCase):

    def setUp(self):
        super(TestCommitSet, self).setUp()
        self.repo = make_repo(self.tmp)

    def test_never_revert_membership(self):
        self.assertEqual(batchsnap.NEVER_REVERT,
                         ("40-01", "40-06", "40-09", "40-14",
                          "41-01", "41-02", "41-03", "41-07", "41-08",
                          "43-02", "43-03", "43-04", "43-05", "43-07",
                          "49-04", "49-05", "49-06", "49-08", "49-09"))
        # Structurally excluded: no NEVER_REVERT id appears in any batch allowlist.
        for batch, plans in batchsnap.BATCH_PLANS.items():
            for plan in plans:
                self.assertNotIn(plan, batchsnap.NEVER_REVERT,
                                 "%s is in BATCH_PLANS[%s]" % (plan, batch))

    def test_batch_plans_match_d06(self):
        self.assertEqual(batchsnap.BATCH_PLANS[1],
                         ("40-02", "40-03", "40-04", "40-05", "40-07", "40-12", "40-13"))
        self.assertEqual(batchsnap.BATCH_PLANS[2], ("40-08", "40-10"))
        self.assertEqual(batchsnap.BATCH_PLANS[3], ("40-11",))

    def test_batch_plans_phase41(self):
        """Batch 4 is exactly the three Wave-1 scorer plans; the Phase-41
        evidence/tooling plans are outside it by construction."""
        self.assertEqual(batchsnap.BATCH_PLANS[4], ("41-04", "41-05", "41-06"))
        for plan in batchsnap.BATCH_PLANS[4]:
            self.assertNotIn(plan, batchsnap.NEVER_REVERT)
        for plan in ("41-01", "41-02", "41-03", "41-07", "41-08"):
            self.assertIn(plan, batchsnap.NEVER_REVERT)
            self.assertNotIn(plan, batchsnap.BATCH_PLANS[4])
        self.assertEqual(len(batchsnap.KNOWN_PLANS), 38)

    def test_batch_plans_phase43(self):
        """Batch 5 is exactly the launch-gate fix and batch 6 exactly the
        conditional retune; every Phase-43 tooling/evidence plan is outside
        every batch by construction."""
        self.assertEqual(batchsnap.BATCH_PLANS[5], ("43-01",))
        self.assertEqual(batchsnap.BATCH_PLANS[6], ("43-06",))
        never43 = ("43-02", "43-03", "43-04", "43-05", "43-07")
        for plan in never43:
            self.assertIn(plan, batchsnap.NEVER_REVERT)
            for batch, plans in batchsnap.BATCH_PLANS.items():
                self.assertNotIn(plan, plans, "%s is in BATCH_PLANS[%s]" % (plan, batch))
        self.assertEqual(set(p for p in batchsnap.KNOWN_PLANS if p.startswith("43-")),
                         set("43-%02d" % n for n in range(1, 8)))

    def test_batch_plans_phase49(self):
        """Batch 7 is exactly the three pre-measurement fixes and batch 8 exactly
        the conditional targeted fix; every Phase-49 tooling/evidence plan is
        outside every batch by construction."""
        self.assertEqual(batchsnap.BATCH_PLANS[7], ("49-01", "49-02", "49-03"))
        self.assertEqual(batchsnap.BATCH_PLANS[8], ("49-07",))
        never49 = ("49-04", "49-05", "49-06", "49-08", "49-09")
        for plan in never49:
            self.assertIn(plan, batchsnap.NEVER_REVERT)
            for batch, plans in batchsnap.BATCH_PLANS.items():
                self.assertNotIn(plan, plans, "%s is in BATCH_PLANS[%s]" % (plan, batch))
        self.assertEqual(set(p for p in batchsnap.KNOWN_PLANS if p.startswith("49-")),
                         set("49-%02d" % n for n in range(1, 10)))

    def test_commit_set_batch7_fails_on_planted_49_04(self):
        """Mutation proof for the Phase-49 unit: planting the tooling plan 49-04
        into BATCH_PLANS[7] must fail naming 49-04 and NEVER_REVERT; with the
        real allowlist restored the same call emits exactly the three shas."""
        recorded = self.record_all(self.repo, 7)
        with open(recorded) as fh:
            self.assertNotIn("49-04", json.load(fh))  # fixture: no recorded sha
        real = batchsnap.BATCH_PLANS
        try:
            batchsnap.BATCH_PLANS = dict(real)
            batchsnap.BATCH_PLANS[7] = real[7] + ("49-04",)
            with self.assertRaises(batchsnap.BatchError) as ctx:
                batchsnap.commit_set(self.repo, 7, recorded)
            msg = str(ctx.exception)
            self.assertIn("49-04", msg)
            self.assertIn("NEVER_REVERT", msg)
            self.assertNotIn("incomplete", msg.lower())
        finally:
            batchsnap.BATCH_PLANS = real
        emitted = batchsnap.commit_set(self.repo, 7, recorded)
        self.assertEqual(len(emitted), 3)

    def test_commit_set_batch4_fails_on_planted_41_01(self):
        """Mutation proof for the Phase-41 unit: planting the ledger/manifest
        plan 41-01 into BATCH_PLANS[4] must fail the command naming 41-01 and
        NEVER_REVERT; with the real allowlist restored the same call succeeds."""
        recorded = self.record_all(self.repo, 4)
        with open(recorded) as fh:
            self.assertNotIn("41-01", json.load(fh))  # fixture: no recorded sha
        real = batchsnap.BATCH_PLANS
        try:
            batchsnap.BATCH_PLANS = dict(real)
            batchsnap.BATCH_PLANS[4] = real[4] + ("41-01",)
            with self.assertRaises(batchsnap.BatchError) as ctx:
                batchsnap.commit_set(self.repo, 4, recorded)
            msg = str(ctx.exception)
            self.assertIn("41-01", msg)
            self.assertIn("NEVER_REVERT", msg)
            self.assertNotIn("incomplete", msg.lower())
        finally:
            batchsnap.BATCH_PLANS = real
        emitted = batchsnap.commit_set(self.repo, 4, recorded)
        self.assertEqual(len(emitted), 3)

    def test_commit_set_batch5_fails_on_planted_43_02(self):
        """Mutation proof for the Phase-43 unit: planting the tooling plan 43-02
        into BATCH_PLANS[5] must fail naming 43-02 and NEVER_REVERT; with the
        real allowlist restored the same call emits exactly the 43-01 sha."""
        recorded = self.record_all(self.repo, 5)
        with open(recorded) as fh:
            self.assertNotIn("43-02", json.load(fh))  # fixture: no recorded sha
        real = batchsnap.BATCH_PLANS
        try:
            batchsnap.BATCH_PLANS = dict(real)
            batchsnap.BATCH_PLANS[5] = real[5] + ("43-02",)
            with self.assertRaises(batchsnap.BatchError) as ctx:
                batchsnap.commit_set(self.repo, 5, recorded)
            msg = str(ctx.exception)
            self.assertIn("43-02", msg)
            self.assertIn("NEVER_REVERT", msg)
            self.assertNotIn("incomplete", msg.lower())
        finally:
            batchsnap.BATCH_PLANS = real
        emitted = batchsnap.commit_set(self.repo, 5, recorded)
        self.assertEqual(len(emitted), 1)

    def test_commit_set_excludes_40_01_by_identity_not_subject(self):
        """R3 regression: the exact commit a subject selector would have swept in.

        Real subject (no plan tag), real touched path under plugins/vibe-check/.
        Reverting it would destroy the append-only SUPERSESSIONS ledger and add a
        third commit to a path whose own gate requires exactly two.
        """
        recorded = os.path.join(self.tmp, "PLAN-COMMITS.json")
        batch_shas = []
        for plan in batchsnap.BATCH_PLANS[1]:
            sha = make_commit(self.repo, plan)
            batch_shas.append(sha)
            self.assertEqual(batchsnap.record_commit(self.repo, plan, sha, recorded), 0)
        ledger_sha = make_commit(self.repo, "40-01", subject=LEDGER_SUBJECT,
                                 path=LEDGER_PATH)
        self.assertEqual(batchsnap.record_commit(self.repo, "40-01", ledger_sha, recorded), 0)
        tooling_sha = make_commit(self.repo, "40-06")
        self.assertEqual(batchsnap.record_commit(self.repo, "40-06", tooling_sha, recorded), 0)

        # Fixture integrity: the decoy really is untagged and really does touch a
        # file under plugins/vibe-check/ -- i.e. it defeats BOTH old heuristics.
        subj = git(self.repo, "log", "-1", "--format=%s", ledger_sha).stdout.strip()
        self.assertEqual(subj, LEDGER_SUBJECT)
        self.assertNotIn("(40-01)", subj)
        touched = git(self.repo, "show", "--name-only", "--format=", ledger_sha).stdout
        self.assertIn("plugins/vibe-check/", touched)
        # Fixture integrity: all seven batch-1 members are recorded (A3) -- with
        # fewer, commit_set exits 1 on the completeness check and never reaches
        # the allowlist assertion this test exists to make.
        with open(recorded) as fh:
            data = json.load(fh)
        self.assertEqual(sorted(k for k in data if k in batchsnap.BATCH_PLANS[1]),
                         sorted(batchsnap.BATCH_PLANS[1]))
        self.assertEqual(len(batch_shas), 7)
        self.assertEqual(len(set(batch_shas)), 7)

        emitted = batchsnap.commit_set(self.repo, 1, recorded)
        self.assertEqual(sorted(emitted), sorted(batch_shas))
        self.assertNotIn(ledger_sha, emitted)
        self.assertNotIn(tooling_sha, emitted)

    def test_commit_set_fails_on_never_revert_in_allowlist(self):
        """A typo in the allowlist must fail the command, not revert evidence.

        This isolates the ALLOWLIST guard: 40-01 is wrongly listed in
        BATCH_PLANS[1] but has NO recorded sha, so there is nothing for the
        emission guard downstream to catch. Only the allowlist assertion can
        refuse here -- and it must refuse rather than reporting 40-01 as merely
        'unrecorded', which would send the owner off to record the very commit
        that must never enter a revert set.
        """
        recorded = self.record_all(self.repo, 1)
        with open(recorded) as fh:
            self.assertNotIn("40-01", json.load(fh))  # fixture: no recorded sha
        real = batchsnap.BATCH_PLANS
        try:
            batchsnap.BATCH_PLANS = dict(real)
            batchsnap.BATCH_PLANS[1] = real[1] + ("40-01",)
            with self.assertRaises(batchsnap.BatchError) as ctx:
                batchsnap.commit_set(self.repo, 1, recorded)
            msg = str(ctx.exception)
            self.assertIn("40-01", msg)
            self.assertIn("NEVER_REVERT", msg)
            # Specifically NOT the unrecorded-plan reason.
            self.assertNotIn("incomplete", msg.lower())
        finally:
            batchsnap.BATCH_PLANS = real
        # The guard tripped on the mutation only: with the real allowlist
        # restored the same call succeeds, so the assertion is not vacuous.
        self.assertEqual(len(batchsnap.commit_set(self.repo, 1, recorded)), 7)

    def test_commit_set_fails_on_sha_recorded_under_never_revert_plan(self):
        """The emission guard, isolated: BATCH_PLANS is CORRECT here.

        The same sha is attributed to both a batch plan and 40-01 in the recorded
        file, so the allowlist guard sees nothing wrong and only the emission
        assertion can refuse. Two guards, two distinct defects: one catches a
        typo in the allowlist, this one catches a mis-recorded identity.
        """
        recorded = os.path.join(self.tmp, "PLAN-COMMITS.json")
        shared = make_commit(self.repo, "40-04", subject=LEDGER_SUBJECT,
                             path=LEDGER_PATH)
        for plan in batchsnap.BATCH_PLANS[1]:
            sha = shared if plan == "40-04" else make_commit(self.repo, plan)
            self.assertEqual(batchsnap.record_commit(self.repo, plan, sha, recorded), 0)
        # record_commit refuses cross-plan duplicates, so this is written
        # directly -- the defect is a recorded file that is already wrong.
        with open(recorded) as fh:
            data = json.load(fh)
        data["40-01"] = [shared]
        write(recorded, json.dumps(data))
        # Fixture integrity: the allowlist itself is untouched and correct.
        self.assertNotIn("40-01", batchsnap.BATCH_PLANS[1])
        with self.assertRaises(batchsnap.BatchError) as ctx:
            batchsnap.commit_set(self.repo, 1, recorded)
        msg = str(ctx.exception)
        self.assertIn(shared, msg)
        self.assertIn("40-01", msg)
        # Remove the bad attribution and the same call succeeds: the guard
        # tripped on the defect, not on the fixture.
        del data["40-01"]
        write(recorded, json.dumps(data))
        self.assertEqual(len(batchsnap.commit_set(self.repo, 1, recorded)), 7)

    def test_commit_set_fails_on_unrecorded_plan(self):
        recorded = self.record_all(self.repo, 1, skip=("40-05",))
        with self.assertRaises(batchsnap.BatchError) as ctx:
            batchsnap.commit_set(self.repo, 1, recorded)
        self.assertIn("40-05", str(ctx.exception))
        # The guard trips only on the gap: record 40-05 and it passes.
        sha = make_commit(self.repo, "40-05")
        self.assertEqual(batchsnap.record_commit(self.repo, "40-05", sha, recorded), 0)
        self.assertEqual(len(batchsnap.commit_set(self.repo, 1, recorded)), 7)

    def test_commit_set_fails_on_missing_sha(self):
        recorded = self.record_all(self.repo, 1)
        with open(recorded) as fh:
            data = json.load(fh)
        good = data["40-04"]
        data["40-04"] = ["b" * 40]
        write(recorded, json.dumps(data))
        with self.assertRaises(batchsnap.BatchError) as ctx:
            batchsnap.commit_set(self.repo, 1, recorded)
        msg = str(ctx.exception)
        self.assertIn("b" * 40, msg)
        # Pin WHICH assertion refused: any refusal would satisfy a bare
        # assertRaises, including one raised for an unrelated reason.
        self.assertIn("does not exist in this repo", msg)
        # And the guard tripped on the bad sha only.
        data["40-04"] = good
        write(recorded, json.dumps(data))
        self.assertEqual(len(batchsnap.commit_set(self.repo, 1, recorded)), 7)

    def test_commit_set_is_revert_order(self):
        recorded = os.path.join(self.tmp, "PLAN-COMMITS.json")
        order = []
        for plan in batchsnap.BATCH_PLANS[1]:
            sha = make_commit(self.repo, plan)
            order.append(sha)
            batchsnap.record_commit(self.repo, plan, sha, recorded)
        emitted = batchsnap.commit_set(self.repo, 1, recorded)
        # Newest-first == reverse of commit order: the owner pastes this straight
        # into `git revert --no-commit` and the order is already correct.
        self.assertEqual(emitted, list(reversed(order)))

    def test_commit_set_no_duplicates(self):
        recorded = self.record_all(self.repo, 1)
        emitted = batchsnap.commit_set(self.repo, 1, recorded)
        self.assertEqual(len(emitted), len(set(emitted)))

    def test_commit_set_unknown_batch(self):
        recorded = self.record_all(self.repo, 1)
        with self.assertRaises(batchsnap.BatchError):
            batchsnap.commit_set(self.repo, 9, recorded)

    def test_commit_set_cli_prints_one_sha_per_line(self):
        recorded = self.record_all(self.repo, 1)
        proc = subprocess.run(
            [sys.executable, BATCHSNAP_PY, "commit-set", "--batch", "1",
             "--recorded", recorded, "--repo", self.repo],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        lines = [l for l in proc.stdout.strip().splitlines() if re.fullmatch(r"[0-9a-f]{40}", l)]
        self.assertEqual(len(lines), 7, proc.stdout)

    def test_commit_set_cli_exits_one_on_unrecorded(self):
        recorded = self.record_all(self.repo, 1, skip=("40-13",))
        proc = subprocess.run(
            [sys.executable, BATCHSNAP_PY, "commit-set", "--batch", "1",
             "--recorded", recorded, "--repo", self.repo],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("40-13", proc.stdout)


class TestRecordCommit(SnapCase):

    def setUp(self):
        super(TestRecordCommit, self).setUp()
        self.repo = make_repo(self.tmp)
        self.recorded = os.path.join(self.tmp, "PLAN-COMMITS.json")

    def test_creates_file_when_absent(self):
        sha = make_commit(self.repo, "40-02")
        self.assertFalse(os.path.exists(self.recorded))
        self.assertEqual(batchsnap.record_commit(self.repo, "40-02", sha, self.recorded), 0)
        with open(self.recorded) as fh:
            self.assertEqual(json.load(fh), {"40-02": [sha]})

    def test_shape_matches_existing_plan_commits_file(self):
        """The real file is {plan-id: [full-sha, ...]} -- match it exactly."""
        real = os.path.join(os.path.abspath(os.path.join(HERE, "..", "..", "..")),
                            "docs", "design", "b3-ground-truth", "runs-v2.10-phase40",
                            "PLAN-COMMITS.json")
        with open(real) as fh:
            existing = json.load(fh)
        self.assertIsInstance(existing, dict)
        for plan, shas in existing.items():
            self.assertRegex(plan, r"^40-\d\d$")
            self.assertIsInstance(shas, list)
            for sha in shas:
                self.assertRegex(sha, r"^[0-9a-f]{40}$")
        # 40-02 recorded only its feature commit; later plans recorded every commit
        # including the RED test commits. commit_set must accept either shape.
        self.assertEqual(len(existing["40-02"]), 1)
        self.assertGreater(len(existing["40-03"]), 1)
        # A3: 40-06 is in NEVER_REVERT and does NOT record its own commits.
        for plan in batchsnap.NEVER_REVERT:
            self.assertNotIn(plan, existing)

    def test_shape_matches_phase41_plan_commits_file(self):
        """Phase 41's recorded file: exactly the batch-4 plans, full shas, and no
        NEVER_REVERT plan recorded."""
        real = os.path.join(os.path.abspath(os.path.join(HERE, "..", "..", "..")),
                            "docs", "design", "b3-ground-truth", "runs-v2.10-phase41",
                            "PLAN-COMMITS.json")
        with open(real) as fh:
            existing = json.load(fh)
        self.assertIsInstance(existing, dict)
        self.assertEqual(sorted(existing), sorted(batchsnap.BATCH_PLANS[4]))
        for plan, shas in existing.items():
            self.assertRegex(plan, r"^41-\d\d$")
            self.assertIsInstance(shas, list)
            self.assertGreaterEqual(len(shas), 1)
            for sha in shas:
                self.assertRegex(sha, r"^[0-9a-f]{40}$")
        for plan in batchsnap.NEVER_REVERT:
            self.assertNotIn(plan, existing)

    def test_record_commit_refuses_unknown_plan_id(self):
        """The allowlist is generic: out-of-range Phase-41 ids and other phases
        are refused with 'unknown plan id'; a real Phase-41 id is accepted."""
        sha = make_commit(self.repo, "41-04")
        for bad in ("41-09", "42-01"):
            proc = subprocess.run(
                [sys.executable, BATCHSNAP_PY, "record-commit", "--plan", bad,
                 "--sha", sha, "--recorded", self.recorded, "--repo", self.repo],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
            self.assertEqual(proc.returncode, 1, proc.stdout)
            self.assertIn("unknown plan id", proc.stdout)
        self.assertFalse(os.path.exists(self.recorded))
        self.assertEqual(batchsnap.record_commit(self.repo, "41-04", sha, self.recorded), 0)
        with open(self.recorded) as fh:
            self.assertEqual(json.load(fh), {"41-04": [sha]})

    def test_record_commit_phase49_range(self):
        """49-09 is the last known Phase-49 id; 49-10 is refused as unknown."""
        sha = make_commit(self.repo, "49-09")
        proc = subprocess.run(
            [sys.executable, BATCHSNAP_PY, "record-commit", "--plan", "49-10",
             "--sha", sha, "--recorded", self.recorded, "--repo", self.repo],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("unknown plan id", proc.stdout)
        self.assertFalse(os.path.exists(self.recorded))
        proc = subprocess.run(
            [sys.executable, BATCHSNAP_PY, "record-commit", "--plan", "49-09",
             "--sha", sha, "--recorded", self.recorded, "--repo", self.repo],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        with open(self.recorded) as fh:
            self.assertEqual(json.load(fh), {"49-09": [sha]})

    def test_appends_to_existing_plan(self):
        a = make_commit(self.repo, "40-03")
        b = make_commit(self.repo, "40-03")
        batchsnap.record_commit(self.repo, "40-03", a, self.recorded)
        batchsnap.record_commit(self.repo, "40-03", b, self.recorded)
        with open(self.recorded) as fh:
            self.assertEqual(json.load(fh)["40-03"], [a, b])

    def test_idempotent_for_identical_pair(self):
        sha = make_commit(self.repo, "40-04")
        self.assertEqual(batchsnap.record_commit(self.repo, "40-04", sha, self.recorded), 0)
        self.assertEqual(batchsnap.record_commit(self.repo, "40-04", sha, self.recorded), 0)
        with open(self.recorded) as fh:
            self.assertEqual(json.load(fh)["40-04"], [sha])

    def test_refuses_same_sha_under_two_plans(self):
        sha = make_commit(self.repo, "40-04")
        self.assertEqual(batchsnap.record_commit(self.repo, "40-04", sha, self.recorded), 0)
        self.assertEqual(batchsnap.record_commit(self.repo, "40-05", sha, self.recorded), 1)
        with open(self.recorded) as fh:
            self.assertNotIn("40-05", json.load(fh))

    def test_refuses_nonexistent_sha(self):
        self.assertEqual(batchsnap.record_commit(self.repo, "40-04", "c" * 40,
                                                 self.recorded), 1)

    def test_refuses_unknown_plan_id(self):
        sha = make_commit(self.repo, "40-04")
        self.assertEqual(batchsnap.record_commit(self.repo, "41-09", sha, self.recorded), 1)
        self.assertEqual(batchsnap.record_commit(self.repo, "nonsense", sha,
                                                 self.recorded), 1)

    def test_accepts_never_revert_plan_ids(self):
        """Recording is not reverting: 40-01 records its identity so commit_set
        can ASSERT against it. What NEVER_REVERT forbids is emission."""
        sha = make_commit(self.repo, "40-01")
        self.assertEqual(batchsnap.record_commit(self.repo, "40-01", sha, self.recorded), 0)

    def test_normalizes_short_sha_to_full(self):
        sha = make_commit(self.repo, "40-02")
        self.assertEqual(batchsnap.record_commit(self.repo, "40-02", sha[:8],
                                                 self.recorded), 0)
        with open(self.recorded) as fh:
            self.assertEqual(json.load(fh)["40-02"], [sha])

    def test_cli_exit_codes(self):
        sha = make_commit(self.repo, "40-02")
        ok = subprocess.run(
            [sys.executable, BATCHSNAP_PY, "record-commit", "--plan", "40-02",
             "--sha", sha, "--recorded", self.recorded, "--repo", self.repo],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        bad = subprocess.run(
            [sys.executable, BATCHSNAP_PY, "record-commit", "--plan", "99-99",
             "--sha", sha, "--recorded", self.recorded, "--repo", self.repo],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
        self.assertEqual(bad.returncode, 1, bad.stdout)


# --------------------------------------------------------------------------
# F10 / FL-02 — the PASS artifact
# --------------------------------------------------------------------------

class TestPassArtifact(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def check(self, artifact, make_artifacts=True, **kw):
        path = write_pass(self.tmp, artifact, make_artifacts=make_artifacts)
        return batchsnap.check_pass_artifact(path, **kw)

    def test_well_formed_pass_validates(self):
        ok, reasons = self.check(make_pass())
        self.assertTrue(ok, reasons)
        self.assertEqual(reasons, [])

    def test_missing_verdict(self):
        ok, reasons = self.check(make_pass(verdict=DROP))
        self.assertFalse(ok)
        self.assertIn("missing required key: verdict", reasons)

    def test_fail_verdict_is_not_a_pass(self):
        ok, reasons = self.check(make_pass(verdict="FAIL"))
        self.assertFalse(ok)
        self.assertIn("verdict is FAIL", reasons)

    def test_unknown_verdict(self):
        ok, reasons = self.check(make_pass(verdict="MAYBE"))
        self.assertFalse(ok)
        self.assertIn("verdict not in enum: MAYBE", reasons)

    def test_snapshot_commit_must_match_manifest(self):
        art = make_pass(snapshot_commit="d" * 40)
        path = write_pass(self.tmp, art)
        ok, reasons = batchsnap.check_pass_artifact(path, expect_commit="e" * 40)
        self.assertFalse(ok)
        self.assertTrue(any("snapshot_commit" in r for r in reasons), reasons)
        ok2, reasons2 = batchsnap.check_pass_artifact(path, expect_commit="d" * 40)
        self.assertTrue(ok2, reasons2)

    def test_pass_artifact_rejects_pending_adjudication(self):
        art = make_pass()
        art["runs"][1]["adjudication"] = "pending-assistant"
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("pending-assistant" in r for r in reasons), reasons)

    def test_unknown_adjudication(self):
        art = make_pass()
        art["runs"][0]["adjudication"] = "probably-fine"
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("adjudication" in r for r in reasons), reasons)

    def test_too_few_runs(self):
        art = make_pass()
        art["runs"] = art["runs"][:1]
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("runs" in r and "2" in r for r in reasons), reasons)

    def test_pass_rejects_pass_verdict_with_failed_state_shape(self):
        """FL-02.1 reproduction: every key present, verdict PASS, mechanics FAILED."""
        art = make_pass()
        art["runs"][0]["state_shape"] = "FAIL"
        for key in SCHEMA["run_required"]:
            self.assertIn(key, art["runs"][0])  # key presence alone would accept it
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("state_shape" in r for r in reasons), reasons)

    def test_pass_rejects_pass_verdict_with_false_sha_match(self):
        """FL-02.1 reproduction: tree_diff_sha_match false under a PASS verdict."""
        art = make_pass()
        art["runs"][1]["tree_diff_sha_match"] = False
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("tree_diff_sha_match" in r for r in reasons), reasons)

    def test_sha_match_must_be_boolean_not_truthy_string(self):
        art = make_pass()
        art["runs"][0]["tree_diff_sha_match"] = "true"
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("tree_diff_sha_match" in r for r in reasons), reasons)

    def test_state_shape_must_be_in_enum(self):
        art = make_pass()
        art["runs"][0]["state_shape"] = "ok"
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("state_shape" in r for r in reasons), reasons)

    def test_pass_rejects_duplicate_run_identity(self):
        """FL-02.2: two runs cannot both claim (diff, run_index)."""
        art = make_pass()
        art["runs"][1]["diff"] = art["runs"][0]["diff"]
        art["runs"][1]["run_index"] = art["runs"][0]["run_index"]
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("duplicate run identity" in r for r in reasons), reasons)

    def test_same_diff_different_index_is_fine(self):
        art = make_pass()
        art["runs"][1]["diff"] = art["runs"][0]["diff"]
        art["runs"][1]["run_index"] = 2
        ok, reasons = self.check(art)
        self.assertTrue(ok, reasons)

    def test_pass_rejects_missing_captured_artifacts(self):
        """FL-02.3: a run with no report/transcript on disk is not scoreable."""
        art = make_pass()
        ok, reasons = self.check(art, make_artifacts=False)
        self.assertFalse(ok)
        self.assertTrue(any("report_path" in r for r in reasons), reasons)
        self.assertTrue(any("transcript_path" in r for r in reasons), reasons)

    def test_pass_rejects_missing_artifact_keys(self):
        art = make_pass()
        del art["runs"][0]["report_path"]
        del art["runs"][0]["transcript_path"]
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("missing required key in run" in r for r in reasons), reasons)

    def test_artifact_path_escaping_the_directory_is_refused(self):
        art = make_pass()
        # Write the legitimate artifacts FIRST, then point one run outside the
        # directory -- the escaping path is never materialized, so this refuses on
        # containment rather than on absence.
        path = write_pass(self.tmp, art)
        art["runs"][0]["report_path"] = "../../../etc/passwd"
        write(path, json.dumps(art, indent=2))
        ok, reasons = batchsnap.check_pass_artifact(path)
        self.assertFalse(ok)
        self.assertTrue(any("report_path" in r and "outside" in r for r in reasons),
                        reasons)

    def test_pass_rejects_failed_trace_validation(self):
        """FL-02.4: any failing trace validation forces FAIL."""
        art = make_pass()
        art["runs"][0]["trace_validation"] = "fail"
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertTrue(any("trace_validation" in r for r in reasons), reasons)

    def test_trace_validation_not_applicable_is_legitimate(self):
        art = make_pass()
        for run in art["runs"]:
            run["trace_validation"] = "not-applicable"
        ok, reasons = self.check(art)
        self.assertTrue(ok, reasons)
        art2 = make_pass()
        for run in art2["runs"]:
            run["trace_validation"] = "pass"
        ok2, reasons2 = self.check(art2)
        self.assertTrue(ok2, reasons2)

    def test_returns_full_reason_list_not_first(self):
        art = make_pass(verdict="MAYBE", recorded_by=DROP)
        art["runs"][0]["state_shape"] = "FAIL"
        art["runs"][1]["tree_diff_sha_match"] = False
        ok, reasons = self.check(art)
        self.assertFalse(ok)
        self.assertGreaterEqual(len(reasons), 4, reasons)
        self.assertTrue(any("verdict" in r for r in reasons))
        self.assertTrue(any("recorded_by" in r for r in reasons))
        self.assertTrue(any("state_shape" in r for r in reasons))
        self.assertTrue(any("tree_diff_sha_match" in r for r in reasons))

    def test_missing_file_is_a_reason_not_a_crash(self):
        ok, reasons = batchsnap.check_pass_artifact(os.path.join(self.tmp, "nope.json"))
        self.assertFalse(ok)
        self.assertTrue(reasons)

    def test_malformed_json_is_a_reason_not_a_crash(self):
        path = os.path.join(self.tmp, "PASS.json")
        write(path, "{not json")
        ok, reasons = batchsnap.check_pass_artifact(path)
        self.assertFalse(ok)
        self.assertTrue(reasons)

    def test_runs_not_a_list(self):
        ok, reasons = self.check(make_pass(runs={}))
        self.assertFalse(ok)
        self.assertTrue(reasons)

    def test_check_pass_cli_exit_codes(self):
        good = write_pass(self.tmp, make_pass())
        proc = subprocess.run([sys.executable, BATCHSNAP_PY, "check-pass", "--file", good],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        bad_dir = os.path.join(self.tmp, "bad")
        os.makedirs(bad_dir)
        bad = write_pass(bad_dir, make_pass(verdict="FAIL"))
        proc = subprocess.run([sys.executable, BATCHSNAP_PY, "check-pass", "--file", bad],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("FAIL", proc.stdout)


# --------------------------------------------------------------------------
# Module conventions
# --------------------------------------------------------------------------

class TestImportSet(unittest.TestCase):

    ALLOWED = {"argparse", "hashlib", "json", "os", "re", "subprocess", "sys"}

    def test_imports_are_exactly_the_allowed_set(self):
        with open(BATCHSNAP_PY) as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
        self.assertEqual(found, self.ALLOWED)

    def test_every_subprocess_run_carries_timeout(self):
        with open(BATCHSNAP_PY) as fh:
            tree = ast.parse(fh.read())
        calls = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and fn.attr == "run"
                    and isinstance(fn.value, ast.Name) and fn.value.id == "subprocess"):
                continue
            calls += 1
            kw = {k.arg: k.value for k in node.keywords}
            self.assertIn("timeout", kw, "subprocess.run at line %d has no timeout"
                          % node.lineno)
            self.assertEqual(kw["timeout"].value, 120,
                             "subprocess.run at line %d: timeout must be 120" % node.lineno)
        self.assertGreater(calls, 0, "found no subprocess.run calls -- test is vacuous")

    def test_no_subject_string_matching(self):
        """R3: selection is by recorded identity; no subject heuristic anywhere."""
        with open(BATCHSNAP_PY) as fh:
            lines = fh.read().splitlines()
        tree = ast.parse("\n".join(lines))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    docstrings.update(doc.splitlines())
        offenders = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "subject" not in stripped.lower():
                continue
            if stripped.startswith("#") or line in docstrings or stripped in (
                    s.strip() for s in docstrings):
                continue
            offenders.append((i, line))
        self.assertEqual(offenders, [], "subject matching in code: %r" % offenders)
        # Fixture integrity: the word DOES appear in the module (in comments and
        # docstrings explaining the defect), so the scan is not looking at nothing.
        self.assertTrue(any("subject" in l.lower() for l in lines))

    def test_schema_fixture_parses_and_carries_required_blocks(self):
        for key in ("manifest_required", "pass_artifact_required", "verdict_enum",
                    "run_required", "adjudication_enum", "state_shape_enum",
                    "trace_validation_enum", "runs_required_per_batch"):
            self.assertIn(key, SCHEMA)
        self.assertIn("snapshot_commit", SCHEMA["manifest_required"])
        self.assertEqual(SCHEMA["verdict_enum"], ["PASS", "FAIL"])
        # FL-02: the mechanical keys are in run_required AND have value constraints.
        for key in ("report_path", "transcript_path", "trace_validation"):
            self.assertIn(key, SCHEMA["run_required"])

    def test_never_revert_constant_carries_a_reason_per_entry(self):
        with open(BATCHSNAP_PY) as fh:
            lines = fh.read().splitlines()
        # The COMMENT BLOCK immediately preceding the assignment -- not the first
        # docstring mention, which would make this assertion vacuous.
        assign = [i for i, l in enumerate(lines) if l.startswith("NEVER_REVERT = ")]
        self.assertEqual(len(assign), 1, "NEVER_REVERT is not assigned exactly once")
        i = assign[0]
        start = i
        while start > 0 and lines[start - 1].lstrip().startswith("#"):
            start -= 1
        # COMMENT ONLY -- the assignment line names every plan id by itself, so
        # including it would make the per-plan assertions vacuous.
        block = "\n".join(lines[start:i])
        self.assertGreater(i - start, 3, "NEVER_REVERT carries no comment block")
        for plan in ("40-01", "40-06", "40-09", "40-14"):
            self.assertIn(plan, block, "no reason naming %s" % plan)
        for word in ("ledger", "tooling", "closing"):
            self.assertIn(word, block.lower(), "no reason naming %r near NEVER_REVERT" % word)


class TestFailClosed(unittest.TestCase):
    """D-13 GATE semantics: every ambiguity exits non-zero."""

    def _run(self, *argv):
        return subprocess.run([sys.executable, BATCHSNAP_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, timeout=60)

    def test_no_subcommand_exits_two(self):
        self.assertEqual(self._run().returncode, 2)

    def test_unknown_subcommand_exits_two(self):
        self.assertEqual(self._run("frobnicate").returncode, 2)

    def test_missing_required_arg_exits_two(self):
        self.assertEqual(self._run("verify").returncode, 2)
        self.assertEqual(self._run("check-pass").returncode, 2)
        self.assertEqual(self._run("commit-set", "--batch", "1").returncode, 2)

    def test_nonexistent_snapshot_exits_two(self):
        self.assertEqual(self._run("verify", "--snap", "/nonexistent/snap").returncode, 2)


class TestNeverEcho(SnapCase):
    """Reasons name plugin-internal paths, never repo CONTENT."""

    def test_sentinel_content_never_appears_in_verify_output(self):
        repo = make_repo(self.tmp)
        sentinel = "SENTINELsecretpayload42"
        write(os.path.join(repo, "plugins", "vibe-check", "agents", "fix.md"),
              "# fix agent\n%s\n" % sentinel)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "plant sentinel")
        _, snap = self.build(repo)
        clean = self.verify(snap)
        self.assertEqual(clean.returncode, 0, clean.stdout)
        self.assertNotIn(sentinel, clean.stdout)
        target = os.path.join(snap, batchsnap.PLUGIN_SUBDIR, "agents", "fix.md")
        os.chmod(target, 0o644)
        with open(target, "a") as fh:
            fh.write("%s-tampered\n" % sentinel)
        os.chmod(target, 0o444)
        dirty = self.verify(snap)
        self.assertEqual(dirty.returncode, 1, dirty.stdout)
        self.assertIn("agents/fix.md", dirty.stdout)
        self.assertNotIn(sentinel, dirty.stdout)


if __name__ == "__main__":
    unittest.main()
