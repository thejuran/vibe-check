"""Tests for gitsnap.py — before/after git-state fingerprint in real temp repos.

Behaviour tests run the CLI as a subprocess with global and system git config
switched off (gitfixture.helper_env). Mutant tests run `gitsnap.run` in-process
with one component collector patched to a constant, first assert that the real
collector would have seen a difference (so the patch genuinely removes signal),
then show the named case is no longer detected — each component is proven to
be load-bearing.
"""

import ast
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import gitsnap  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from gitfixture import git, write  # noqa: E402

GITSNAP = os.path.join(SCRIPTS_DIR, "gitsnap.py")


class GitsnapCase(unittest.TestCase):
    """Base: a temp repo on main with one commit, a second branch `other`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = gitfixture.make_repo(self.tmp)
        write(self.repo, "f.txt", "one\n")
        git(self.repo, "add", "--", "f.txt")
        git(self.repo, "commit", "-q", "-m", "init")
        git(self.repo, "branch", "other")
        self.snap = os.path.join(self.tmp, "snaps", "before.json")

    def tearDown(self):
        self._tmp.cleanup()

    # ------------------------------------------------------------ helpers

    def cli(self, *args, root=None):
        proc = subprocess.run(
            [sys.executable, GITSNAP, *args], cwd=self.tmp,
            env=gitfixture.helper_env(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=120)
        return proc

    def take(self, root=None):
        proc = self.cli("take", "--root", root or self.repo, "--out", self.snap)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def compare(self, root=None, before=None):
        return self.cli("compare", "--root", root or self.repo,
                        "--before", before or self.snap)

    def run_inproc(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, gitfixture.helper_env(), clear=True), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gitsnap.run(list(argv))
        return code, out.getvalue()

    def take_inproc(self):
        code, out = self.run_inproc("take", "--root", self.repo, "--out", self.snap)
        self.assertEqual(code, 0, out)

    def compare_inproc(self):
        return self.run_inproc("compare", "--root", self.repo, "--before", self.snap)

    def make_stash(self, content="stashed edit\n"):
        write(self.repo, "f.txt", content)
        git(self.repo, "stash", "push", "-q", "-m", "owner wip")


class TestTake(GitsnapCase):

    def test_take_writes_all_components_and_creates_parent(self):
        self.take()
        with open(self.snap) as fh:
            data = json.load(fh)
        for key in ("head", "symref", "index_sha256", "stash", "refs_sha256",
                    "refs", "head_reflog_count", "in_progress"):
            self.assertIn(key, data)
        self.assertEqual(data["symref"], "refs/heads/main")
        self.assertIn("refs/heads/other", data["refs"])
        self.assertEqual(data["stash"], [])
        self.assertEqual(data["in_progress"], [])
        self.assertGreaterEqual(data["head_reflog_count"], 1)

    def test_take_outside_a_repo_exits_2(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        proc = self.cli("take", "--root", plain, "--out", self.snap)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(os.path.exists(self.snap))

    def test_take_unwritable_out_exits_2(self):
        blocker = os.path.join(self.tmp, "blocker")
        write(self.tmp, "blocker", "x")
        proc = self.cli("take", "--root", self.repo,
                        "--out", os.path.join(blocker, "snap.json"))
        self.assertEqual(proc.returncode, 2)

    def test_usage_error_exits_2(self):
        self.assertEqual(self.cli("take", "--root", self.repo).returncode, 2)
        self.assertEqual(self.cli().returncode, 2)


class TestNoChange(GitsnapCase):

    def test_nothing_between_is_same(self):
        self.take()
        proc = self.compare()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(proc.stdout, "")

    def test_read_only_git_activity_is_not_a_change(self):
        # Touch the tracked file so `git status` has stat data to refresh in
        # .git/index — the snapshot must not hash those bytes.
        self.take()
        os.utime(os.path.join(self.repo, "f.txt"), (1, 1))
        git(self.repo, "status")
        git(self.repo, "diff")
        git(self.repo, "log", "--oneline")
        os.utime(os.path.join(self.repo, "f.txt"), None)
        git(self.repo, "status", "--porcelain")
        proc = self.compare()
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_review_scratch_under_turingmind_is_not_a_change(self):
        self.take()
        write(self.repo, ".turingmind/blocks.md", "scratch\n")
        write(self.repo, ".turingmind/state/x.json", "{}\n")
        write(self.repo, "f.txt", "unstaged edit\n")
        proc = self.compare()
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_unborn_repo_takes_and_compares_same(self):
        repo = gitfixture.make_repo(os.path.join(self.tmp, "u"))
        self.take(root=repo)
        with open(self.snap) as fh:
            self.assertIsNone(json.load(fh)["head"])
        proc = self.compare(root=repo)
        self.assertEqual(proc.returncode, 0, proc.stdout)


class TestDetectsChange(GitsnapCase):

    def assertChanged(self, needle):
        proc = self.compare()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(needle, proc.stdout)
        return proc

    def test_stash_pop_then_restash_same_content_is_detected(self):
        # The Phase 43 incident: a stash popped, then "restored" by re-stashing
        # the same content. Same count, same diff — but a new stash commit.
        self.make_stash()
        self.take()
        git(self.repo, "stash", "pop", "-q")
        git(self.repo, "stash", "push", "-q", "-m",
            "restore: undo accidental stash pop")
        proc = self.assertChanged("stash")
        self.assertIn("1 → 1 entries", proc.stdout)

    def test_stash_drop_is_detected(self):
        self.make_stash()
        self.take()
        git(self.repo, "stash", "drop", "-q")
        self.assertChanged("stash list changed (1 → 0 entries)")

    def test_commit_moves_head(self):
        self.take()
        write(self.repo, "f.txt", "two\n")
        git(self.repo, "commit", "-q", "-am", "second")
        self.assertChanged("HEAD moved")

    def test_checkout_round_trip_grows_reflog(self):
        self.take()
        git(self.repo, "checkout", "-q", "other")
        git(self.repo, "checkout", "-q", "main")
        proc = self.assertChanged("HEAD reflog grew by 2 entries")
        self.assertNotIn("HEAD moved", proc.stdout)

    def test_git_add_changes_staged_files(self):
        self.take()
        write(self.repo, "f.txt", "staged\n")
        git(self.repo, "add", "f.txt")
        self.assertChanged("staged files changed")

    def test_branch_delete_is_detected(self):
        git(self.repo, "branch", "x")
        self.take()
        git(self.repo, "branch", "-D", "x")
        self.assertChanged("refs/heads/x deleted")

    def test_tag_create_is_detected(self):
        self.take()
        git(self.repo, "tag", "v9")
        self.assertChanged("refs/tags/v9 created")

    def test_switch_at_same_commit_is_branch_switch(self):
        self.take()
        git(self.repo, "switch", "-q", "other")
        self.assertChanged("branch switched main → other")

    def test_merge_in_progress_is_detected(self):
        git(self.repo, "checkout", "-q", "other")
        write(self.repo, "f.txt", "theirs\n")
        git(self.repo, "commit", "-q", "-am", "theirs")
        git(self.repo, "checkout", "-q", "main")
        write(self.repo, "f.txt", "ours\n")
        git(self.repo, "commit", "-q", "-am", "ours")
        self.take()
        git(self.repo, "merge", "other", check=False)
        self.assertChanged("a merge/rebase is now in progress")


class TestRemoteRefsExcluded(GitsnapCase):
    """Remote-tracking refs move on a background fetch; they are not tracked.

    Local namespaces (refs/heads, refs/tags) and lookalike namespaces such as
    refs/remotes-evil/ stay tracked: the exclusion is an exact prefix.
    """

    def assertSame(self):
        proc = self.compare()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout, "", proc.stdout + proc.stderr)
        return proc

    def test_remote_ref_created_is_not_a_change(self):
        self.take()
        git(self.repo, "update-ref", "refs/remotes/origin/x", "HEAD")
        self.assertSame()

    def test_remote_ref_moved_is_not_a_change(self):
        git(self.repo, "update-ref", "refs/remotes/origin/x", "HEAD")
        self.take()
        # A commit object made without touching any local ref or HEAD reflog.
        sha = git(self.repo, "commit-tree", "HEAD^{tree}", "-p", "HEAD",
                  "-m", "fetched").stdout.strip()
        git(self.repo, "update-ref", "refs/remotes/origin/x", sha)
        self.assertSame()

    def test_remote_ref_deleted_is_not_a_change(self):
        git(self.repo, "update-ref", "refs/remotes/origin/x", "HEAD")
        self.take()
        git(self.repo, "update-ref", "-d", "refs/remotes/origin/x")
        self.assertSame()

    def test_real_fetch_is_not_a_change(self):
        # Remote config lives in .git/config and the fetch writes FETCH_HEAD;
        # gitsnap fingerprints neither, so only refs/remotes/* could move.
        bare = os.path.join(self.tmp, "origin.git")
        pusher = os.path.join(self.tmp, "pusher")
        git(self.tmp, "init", "-q", "--bare", "-b", "main", bare)
        git(self.repo, "remote", "add", "origin", bare)
        git(self.repo, "push", "-q", "origin", "main")
        git(self.tmp, "clone", "-q", bare, pusher)
        self.take()
        write(pusher, "g.txt", "upstream\n")
        git(pusher, "add", "--", "g.txt")
        git(pusher, "commit", "-q", "-m", "upstream")
        git(pusher, "push", "-q", "origin", "main")
        git(pusher, "push", "-q", "origin", "HEAD:refs/heads/newbranch")
        git(self.repo, "fetch", "-q", "origin")
        self.assertSame()

    def test_snapshot_omits_remote_refs(self):
        git(self.repo, "update-ref", "refs/remotes/origin/x", "HEAD")
        self.take()
        with open(self.snap) as fh:
            data = json.load(fh)
        self.assertFalse(
            [k for k in data["refs"] if k.startswith("refs/remotes/")],
            data["refs"])
        self.assertIn("refs/heads/main", data["refs"])

    def test_remotes_lookalike_ref_is_still_tracked(self):
        self.take()
        git(self.repo, "update-ref", "refs/remotes-evil/x", "HEAD")
        proc = self.compare()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("refs/remotes-evil/x created", proc.stdout)

    def test_local_branch_created_is_still_detected(self):
        self.take()
        git(self.repo, "update-ref", "refs/heads/x", "HEAD")
        proc = self.compare()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("refs/heads/x created", proc.stdout)


class TestCannotConfirm(GitsnapCase):

    def test_missing_before_file_exits_2(self):
        self.assertEqual(self.compare().returncode, 2)

    def test_garbled_before_file_exits_2(self):
        write(self.tmp, "snaps/before.json", "not json{")
        self.assertEqual(self.compare().returncode, 2)

    def test_wrong_shape_before_file_exits_2(self):
        write(self.tmp, "snaps/before.json", json.dumps({"head": "abc"}))
        self.assertEqual(self.compare().returncode, 2)

    def test_compare_outside_a_repo_exits_2(self):
        self.take()
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        self.assertEqual(self.compare(root=plain).returncode, 2)


class TestGitsnapMutants(GitsnapCase):
    """Each component removed in turn makes its own case go undetected.

    Pattern: run the event under the real collectors (detected, exit 1), assert
    the real collector's value differs from the mutant constant, then re-take
    with the collector patched, repeat the event and show exit 0.
    """

    def mutant_flips(self, name, constant, event):
        self.take_inproc()
        event()
        code, out = self.compare_inproc()
        self.assertEqual(code, 1, "real collectors must detect: " + out)
        with mock.patch.dict(os.environ, gitfixture.helper_env(), clear=True):
            self.assertNotEqual(getattr(gitsnap, name)(self.repo), constant)
        with mock.patch.object(gitsnap, name, return_value=constant):
            self.take_inproc()
            event()
            code, out = self.compare_inproc()
        self.assertEqual(code, 0, "mutant %s should go blind: %s" % (name, out))

    def test_mutant_stash_component_dropped_misses_stash_drop(self):
        # A drop touches nothing but the stash list, so only the stash
        # component can see it.
        def drop():
            git(self.repo, "stash", "drop", "-q")
        self.make_stash("first\n")
        self.make_stash("second\n")
        self.make_stash("third\n")
        self.mutant_flips("collect_stash", [], drop)

    def test_mutant_stash_component_dropped_loses_phase43_stash_line(self):
        # The re-stash in the Phase 43 shape also runs an internal reset that
        # grows the HEAD reflog, so the reflog component catches it too. The
        # stash component is still what NAMES the incident: without it the
        # "stash list changed" line disappears.
        def pop_and_restash():
            git(self.repo, "stash", "pop", "-q")
            git(self.repo, "stash", "push", "-q", "-m",
                "restore: undo accidental stash pop")
        self.make_stash()
        self.take_inproc()
        pop_and_restash()
        code, out = self.compare_inproc()
        self.assertEqual(code, 1)
        self.assertIn("stash list changed (1 → 1 entries; contents differ)", out)
        with mock.patch.object(gitsnap, "collect_stash", return_value=[]):
            self.take_inproc()
            pop_and_restash()
            code, out = self.compare_inproc()
        self.assertNotIn("stash", out)

    def test_mutant_reflog_component_constant_misses_checkout_round_trip(self):
        def round_trip():
            git(self.repo, "checkout", "-q", "other")
            git(self.repo, "checkout", "-q", "main")
        self.mutant_flips("collect_head_reflog_count", 7, round_trip)

    def test_mutant_index_component_constant_misses_git_add(self):
        counter = [0]

        def add():
            counter[0] += 1
            write(self.repo, "f.txt", "staged %d\n" % counter[0])
            git(self.repo, "add", "f.txt")
        self.mutant_flips("collect_index_sha256", "0" * 64, add)

    def test_mutant_no_remote_exclusion_halts_on_fetch(self):
        def event():
            git(self.repo, "update-ref", "refs/remotes/origin/x", "HEAD")
        self.take_inproc()
        event()
        code, out = self.compare_inproc()
        self.assertEqual(code, 0, "real code must ignore remotes: " + out)
        self.assertNotEqual(gitsnap.EXCLUDED_REF_PREFIXES, ())
        git(self.repo, "update-ref", "-d", "refs/remotes/origin/x")
        with mock.patch.object(gitsnap, "EXCLUDED_REF_PREFIXES", ()):
            self.take_inproc()
            event()
            code, out = self.compare_inproc()
        self.assertEqual(code, 1, "mutant without exclusion must halt: " + out)
        self.assertIn("refs/remotes/origin/x created", out)

    def test_mutant_substring_exclusion_hides_lookalike_ref(self):
        def event():
            git(self.repo, "update-ref", "refs/remotes-evil/x", "HEAD")
        self.take_inproc()
        event()
        code, out = self.compare_inproc()
        self.assertEqual(code, 1, "real code must track lookalike: " + out)
        self.assertIn("refs/remotes-evil/x created", out)
        self.assertNotEqual(gitsnap.EXCLUDED_REF_PREFIXES, ("refs/remotes",))
        git(self.repo, "update-ref", "-d", "refs/remotes-evil/x")
        with mock.patch.object(gitsnap, "EXCLUDED_REF_PREFIXES",
                               ("refs/remotes",)):
            self.take_inproc()
            event()
            code, out = self.compare_inproc()
        self.assertEqual(code, 0, "slashless mutant should go blind: " + out)


class TestModuleShape(unittest.TestCase):
    """Import set and read-only discipline stated in the docstring."""

    def setUp(self):
        with open(os.path.join(SCRIPTS_DIR, "gitsnap.py")) as fh:
            self.src = fh.read()
        self.tree = ast.parse(self.src)

    def test_import_set_is_exact(self):
        names = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        self.assertEqual(names, {"argparse", "hashlib", "json", "os",
                                 "subprocess", "sys"})

    def test_every_subprocess_run_has_timeout_and_no_shell(self):
        calls = [n for n in ast.walk(self.tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "run"
                 and getattr(n.func.value, "id", None) == "subprocess"]
        self.assertTrue(calls)
        for call in calls:
            kws = {k.arg for k in call.keywords}
            self.assertIn("timeout", kws)
            self.assertNotIn("shell", kws)

    def test_git_runner_disables_optional_locks(self):
        self.assertIn('"--no-optional-locks"', self.src)


if __name__ == "__main__":
    unittest.main()
