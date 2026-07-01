"""Tests for guard.py — the single tested path-containment check (Fable A7/B2, A10/B3).

Locks the exact defects the inline copies had, so they can never drift back:
  - empty $ROOT fail-open (the bash `case "$REAL/" in "/"*` degeneration)
  - missing-path intolerance (BSD realpath downgrading deleted-file findings)
  - sibling-dir masquerade (/repo-other vs /repo)
  - symlink escape through an in-repo link
plus the CLI contract (exit codes, multi-path all-must-pass, no path echo).
"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guard  # noqa: E402  (sibling module under test)

GUARD_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard.py")


class TestContained(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        os.makedirs(os.path.join(self.root, "src"))
        with open(os.path.join(self.root, "src", "a.py"), "w") as f:
            f.write("x = 1\n")

    def tearDown(self):
        self._tmp.cleanup()

    # --- the B2 fail-open, killed ------------------------------------------ #
    def test_empty_root_refused(self):
        # THE drift bug: the bash copies matched ANY absolute path when $ROOT
        # was empty. guard.py fails closed.
        for root in ("", "   ", None):
            with self.subTest(root=root):
                ok, reason = guard.contained(root, "/etc/passwd")
                self.assertFalse(ok)
                self.assertIn("fail closed", reason)

    def test_nonexistent_root_refused(self):
        ok, _ = guard.contained(os.path.join(self.root, "no-such-dir"), "src/a.py")
        self.assertFalse(ok)

    def test_root_that_is_a_file_refused(self):
        ok, _ = guard.contained(os.path.join(self.root, "src", "a.py"), "a.py")
        self.assertFalse(ok)

    def test_empty_candidate_refused(self):
        for cand in ("", "  ", None):
            with self.subTest(cand=cand):
                ok, _ = guard.contained(self.root, cand)
                self.assertFalse(ok)

    # --- basic containment -------------------------------------------------- #
    def test_relative_in_repo_contained(self):
        ok, reason = guard.contained(self.root, "src/a.py")
        self.assertTrue(ok)
        self.assertEqual(reason, "contained")

    def test_root_itself_contained(self):
        ok, _ = guard.contained(self.root, ".")
        self.assertTrue(ok)

    def test_absolute_inside_contained(self):
        ok, _ = guard.contained(self.root, os.path.join(self.root, "src", "a.py"))
        self.assertTrue(ok)

    def test_absolute_outside_refused(self):
        ok, reason = guard.contained(self.root, "/etc/passwd")
        self.assertFalse(ok)
        # The refusal reason NEVER echoes the candidate path.
        self.assertNotIn("passwd", reason)

    def test_dotdot_traversal_refused(self):
        ok, _ = guard.contained(self.root, "../../etc/passwd")
        self.assertFalse(ok)

    def test_internal_dotdot_that_stays_inside_contained(self):
        ok, _ = guard.contained(self.root, "src/../src/a.py")
        self.assertTrue(ok)

    # --- the B3/A10 missing-path tolerance ---------------------------------- #
    def test_deleted_file_still_judged_lexically(self):
        # A file deleted in the reviewed range is a legal diff-set member; BSD
        # realpath returned empty for it and the old copies downgraded the
        # finding. guard.py judges the lexical position.
        ok, reason = guard.contained(self.root, "src/deleted_in_diff.py")
        self.assertTrue(ok)
        self.assertEqual(reason, "contained")

    def test_missing_path_outside_still_refused(self):
        ok, _ = guard.contained(self.root, "../missing-outside.py")
        self.assertFalse(ok)

    # --- masquerade + symlinks ---------------------------------------------- #
    def test_sibling_dir_masquerade_refused(self):
        # /repo-other must not pass as under /repo (the trailing-separator
        # compare the case-form got right — kept here).
        sibling = self.root + "-other"
        os.makedirs(sibling, exist_ok=True)
        try:
            ok, _ = guard.contained(self.root, sibling)
            self.assertFalse(ok)
        finally:
            os.rmdir(sibling)

    def test_symlink_escape_refused(self):
        # An in-repo symlink pointing outside the root is resolved and refused
        # (the planted `coverage -> /outside` case from deep-review.md T-21-01).
        outside = tempfile.mkdtemp()
        link = os.path.join(self.root, "coverage")
        os.symlink(outside, link)
        try:
            ok, _ = guard.contained(self.root, "coverage/lcov.info")
            self.assertFalse(ok)
        finally:
            os.unlink(link)
            os.rmdir(outside)

    def test_symlink_within_repo_contained(self):
        os.symlink(os.path.join(self.root, "src"),
                   os.path.join(self.root, "srclink"))
        ok, _ = guard.contained(self.root, "srclink/a.py")
        self.assertTrue(ok)

    def test_symlinked_root_normalized(self):
        # A root reached through a symlink (macOS /tmp -> /private/tmp) is
        # realpath'd before the compare, so both sides agree.
        rootlink = self.root + "-link"
        os.symlink(self.root, rootlink)
        try:
            ok, _ = guard.contained(rootlink, "src/a.py")
            self.assertTrue(ok)
        finally:
            os.unlink(rootlink)


class TestCli(unittest.TestCase):
    """The bash call sites branch on the exit code — lock it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        os.makedirs(os.path.join(self.root, "src"))

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, *argv):
        return subprocess.run([sys.executable, GUARD_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=30)

    def test_contained_exits_zero(self):
        proc = self._run("--root", self.root, "--path", "src/a.py")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "contained")

    def test_escape_exits_one(self):
        proc = self._run("--root", self.root, "--path", "../escape")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refused", proc.stdout)

    def test_empty_root_exits_one(self):
        proc = self._run("--root", "", "--path", "src/a.py")
        self.assertEqual(proc.returncode, 1)

    def test_multi_path_all_must_pass(self):
        ok = self._run("--root", self.root,
                       "--path", "src/a.py", "--path", "src/b.py")
        self.assertEqual(ok.returncode, 0)
        mixed = self._run("--root", self.root,
                          "--path", "src/a.py", "--path", "/etc/passwd")
        self.assertEqual(mixed.returncode, 1)
        # One verdict line per path, in order.
        self.assertEqual(len(mixed.stdout.strip().split("\n")), 2)

    def test_usage_error_exits_nonzero(self):
        proc = self._run("--root", self.root)  # no --path
        self.assertNotEqual(proc.returncode, 0)

    def test_rejected_path_never_echoed(self):
        proc = self._run("--root", self.root, "--path", "../../secret-name.txt")
        self.assertNotIn("secret-name", proc.stdout)
        self.assertNotIn("secret-name", proc.stderr)


if __name__ == "__main__":
    unittest.main()
