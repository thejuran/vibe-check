"""Tests for fixstage.py — per-attempt snapshot / seal / undo in real temp repos.

Every git call (test side and fixstage's own) runs with global and system git
config switched off (gitfixture.helper_env). Mutant tests run `fixstage.run`
in-process with one private function patched, and show that the assertion
helper the behaviour test relies on returns False for the mutated run — so each
lock is proven able to trip.
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import fixstage  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from gitfixture import git, write  # noqa: E402

FIXSTAGE = os.path.join(SCRIPTS_DIR, "fixstage.py")
FID = "abcdef0123456789"


class Result(object):
    def __init__(self, code, out, err):
        self.returncode = code
        self.stdout = out
        self.stderr = err


class FixstageCase(unittest.TestCase):
    """Base: a temp repo with one committed file and a finding record."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = gitfixture.make_repo(self.tmp)
        self.lines = ["line %d\n" % i for i in range(1, 41)]
        write(self.repo, "f.txt", "".join(self.lines))
        write(self.repo, "g.txt", "g\n")
        git(self.repo, "add", "--", "f.txt", "g.txt")
        git(self.repo, "commit", "-q", "-m", "init")
        self.record_path = os.path.join(self.tmp, "finding.json")
        self.set_record(["f.txt"])

    def tearDown(self):
        self._tmp.cleanup()

    # ------------------------------------------------------------ helpers

    def set_record(self, paths, fid=FID, **extra):
        record = {"id": fid, "pass_number": 1, "title": "Fix it", "paths": paths}
        record.update(extra)
        with open(self.record_path, "w") as fh:
            json.dump(record, fh)

    def cli(self, *args):
        proc = subprocess.run([sys.executable, FIXSTAGE] + list(args),
                              env=gitfixture.helper_env(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=120)
        return Result(proc.returncode, proc.stdout, proc.stderr)

    def inproc(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, gitfixture.helper_env()), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = fixstage.run(list(args))
        return Result(code, out.getvalue(), err.getvalue())

    def sub(self, name, attempt=None, runner=None):
        args = [name, "--root", self.repo, "--finding-json", self.record_path]
        if attempt is not None:
            args += ["--attempt", attempt]
        return (runner or self.cli)(*args)

    def begin(self):
        res = self.sub("begin")
        self.assertEqual(res.returncode, 0, res.stderr)
        last = res.stdout.strip().splitlines()[-1]
        self.assertTrue(last.startswith("attempt="), res.stdout)
        return last[len("attempt="):]

    def ok(self, name, attempt, runner=None):
        res = self.sub(name, attempt, runner)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res

    def sdir(self):
        return os.path.join(self.repo, ".turingmind", "fixstage", FID)

    def open_id(self):
        path = os.path.join(self.sdir(), "open")
        if not os.path.exists(path):
            return None
        with open(path) as fh:
            return fh.read().strip()

    def manifest(self, attempt):
        with open(os.path.join(self.sdir(), attempt, "manifest.json")) as fh:
            return json.load(fh)

    def manifest_bytes(self, attempt):
        with open(os.path.join(self.sdir(), attempt, "manifest.json"), "rb") as fh:
            return fh.read()

    def read(self, rel):
        with open(os.path.join(self.repo, rel), "rb") as fh:
            return fh.read()

    def edit_line(self, rel, lineno, text):
        lines = self.read(rel).decode().splitlines(True)
        lines[lineno - 1] = text
        write(self.repo, rel, "".join(lines))

    def mode(self, rel):
        return os.stat(os.path.join(self.repo, rel)).st_mode & 0o7777


class TestAttempt(FixstageCase):

    def stale_attempt_refused(self, result, repo, open_before, file_before):
        """The stale-id lock held: exit 1, `open` unchanged, file untouched."""
        with open(os.path.join(repo, "f.txt"), "rb") as fh:
            unchanged = fh.read() == file_before
        return (result.returncode == 1 and self.open_id() == open_before
                and unchanged)

    def test_begin_unique_ids_and_quarantine(self):
        first = self.begin()
        self.assertRegex(first, r"^[0-9a-f]{32}$")
        self.assertEqual(self.open_id(), first)
        res = self.sub("begin")
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = res.stdout.strip().splitlines()
        self.assertEqual(lines[0], "quarantined=%s" % first)
        second = lines[-1][len("attempt="):]
        self.assertNotEqual(first, second)
        self.assertEqual(self.open_id(), second)
        self.assertFalse(os.path.exists(os.path.join(self.sdir(), first)))
        self.assertTrue(os.path.isdir(
            os.path.join(self.sdir(), "closed", first + ".stale")))

    def test_begin_prunes_closed_to_five(self):
        for _ in range(8):
            self.begin()
        self.assertEqual(len(os.listdir(os.path.join(self.sdir(), "closed"))), 5)

    def test_wrong_and_quarantined_ids_refused_without_state_change(self):
        old = self.begin()
        current = self.begin()  # quarantines `old`
        self.ok("snapshot", current)
        before = self.manifest_bytes(current)
        wrong = "0" * 32
        for attempt in (wrong, old):
            for name in ("snapshot", "seal", "undo"):
                with self.subTest(attempt=attempt, name=name):
                    res = self.sub(name, attempt)
                    self.assertEqual(res.returncode, 1, res.stderr)
                    self.assertIn(fixstage.REFUSED_STALE, res.stderr)
                    self.assertEqual(self.manifest_bytes(current), before)
                    self.assertEqual(self.open_id(), current)
        self.assertFalse(os.path.exists(os.path.join(self.sdir(), wrong)))

    def test_snapshot_idempotent_and_sibling_added_later(self):
        a = self.begin()
        pre = self.read("f.txt")
        self.ok("snapshot", a)
        self.edit_line("f.txt", 30, "fixed 30\n")
        self.ok("snapshot", a)  # second call must keep the ORIGINAL pre bytes
        with open(os.path.join(self.sdir(), a, "0.pre"), "rb") as fh:
            self.assertEqual(fh.read(), pre)
        self.set_record(["f.txt", "g.txt"])
        self.ok("snapshot", a)
        paths = [e["path"] for e in self.manifest(a)["paths"]]
        self.assertEqual(paths, ["f.txt", "g.txt"])
        entry = self.manifest(a)["paths"][0]
        self.assertEqual(entry["state"], "tracked")
        self.assertRegex(entry["index_blob"], r"^[0-9a-f]{40}$")
        head = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(self.manifest(a)["head"], head)

    def test_snapshot_states(self):
        write(self.repo, "u.txt", "untracked\n")
        self.set_record(["f.txt", "u.txt", "new.txt"])
        a = self.begin()
        self.ok("snapshot", a)
        states = {e["path"]: e["state"] for e in self.manifest(a)["paths"]}
        self.assertEqual(states, {"f.txt": "tracked", "u.txt": "untracked",
                                  "new.txt": "absent"})
        absent = [e for e in self.manifest(a)["paths"] if e["path"] == "new.txt"]
        self.assertIsNone(absent[0]["index_blob"])
        self.assertFalse(os.path.exists(
            os.path.join(self.sdir(), a, "%d.pre" % absent[0]["n"])))

    def test_snapshot_after_seal_and_second_seal_refused(self):
        a = self.begin()
        self.ok("snapshot", a)
        self.edit_line("f.txt", 30, "fixed 30\n")
        self.ok("seal", a)
        post_file = os.path.join(self.sdir(), a, "0.post")
        with open(post_file, "rb") as fh:
            post = fh.read()
        self.edit_line("f.txt", 30, "edited again\n")
        res = self.sub("snapshot", a)
        self.assertEqual(res.returncode, 1)
        self.assertIn("attempt sealed", res.stderr)
        res = self.sub("seal", a)
        self.assertEqual(res.returncode, 1)
        with open(post_file, "rb") as fh:
            self.assertEqual(fh.read(), post)
        self.assertTrue(self.manifest(a)["sealed"])

    def test_seal_without_snapshot_closes_attempt(self):
        a = self.begin()
        self.ok("snapshot", a)
        self.set_record(["f.txt", "g.txt"])  # g.txt never snapshotted
        res = self.sub("seal", a)
        self.assertEqual(res.returncode, 1)
        self.assertIn("without a pre-edit snapshot", res.stderr)
        self.assertIsNone(self.open_id())
        self.assertTrue(os.path.isdir(
            os.path.join(self.sdir(), "closed", a + ".refused")))

    def test_refusals_create_no_stage_dir(self):
        cases = []
        cases.append(("non-hex id", {"fid": "XYZ12345"}, ["f.txt"], None, 1))
        cases.append(("short id", {"fid": "abc"}, ["f.txt"], None, 1))
        cases.append(("traversal path", {}, ["../x"], None, 1))
        cases.append(("space path", {}, ["a b.txt"], None, 1))
        cases.append(("dash path", {}, ["-x"], None, 1))
        cases.append(("dotgit path", {}, [".git/hooks/pre-commit"], None, 1))
        cases.append(("own state path", {}, [".turingmind/fixstage/x"], None, 1))
        cases.append(("non-normal path", {}, ["./f.txt"], None, 1))
        for label, kw, paths, extra_args, code in cases:
            with self.subTest(label):
                self.set_record(paths, **kw)
                res = self.sub("begin")
                self.assertEqual(res.returncode, code, res.stderr)
                self.assertFalse(os.path.exists(
                    os.path.join(self.repo, ".turingmind")))
        self.set_record(["f.txt"])
        for label, args, code in (
                ("bad attempt", ["snapshot", "--root", self.repo,
                                 "--finding-json", self.record_path,
                                 "--attempt", "../x"], 1),
                ("unknown flag", ["begin", "--root", self.repo,
                                  "--finding-json", self.record_path,
                                  "--title", "x"], 2),
                ("missing attempt", ["seal", "--root", self.repo,
                                     "--finding-json", self.record_path], 2),
                ("begin with attempt", ["begin", "--root", self.repo,
                                        "--finding-json", self.record_path,
                                        "--attempt", "0" * 32], 2),
                ("no subcommand", [], 2),
                ("missing record", ["begin", "--root", self.repo,
                                    "--finding-json",
                                    os.path.join(self.tmp, "nope.json")], 1),
                ("root not top level", ["begin", "--root",
                                        os.path.join(self.repo, ".git"),
                                        "--finding-json", self.record_path], 1)):
            with self.subTest(label):
                res = self.cli(*args)
                self.assertEqual(res.returncode, code, res.stderr)
                self.assertFalse(os.path.exists(
                    os.path.join(self.repo, ".turingmind")))

    def test_snapshot_refuses_symlink(self):
        os.symlink("g.txt", os.path.join(self.repo, "link.txt"))
        self.set_record(["link.txt"])
        a = self.begin()
        res = self.sub("snapshot", a)
        self.assertEqual(res.returncode, 1)
        self.assertIn("not a regular file", res.stderr)

    def _stale_snapshot_scenario(self, runner):
        """A sealed attempt's state reappears on disk after a newer begin."""
        old = self.begin()
        self.ok("snapshot", old)
        self.edit_line("f.txt", 30, "fixed 30\n")
        self.ok("seal", old)
        current = self.begin()  # quarantines `old`
        shutil.copytree(os.path.join(self.sdir(), "closed", old + ".stale"),
                        os.path.join(self.sdir(), old))
        open_before = self.open_id()
        file_before = self.read("f.txt")
        res = self.sub("undo", old, runner=runner)
        return res, open_before, file_before, current

    def test_stale_snapshot_never_used(self):
        res, open_before, file_before, current = \
            self._stale_snapshot_scenario(self.inproc)
        self.assertEqual(open_before, current)
        self.assertTrue(self.stale_attempt_refused(res, self.repo, open_before,
                                                   file_before), res.stderr)

    def test_mutant_require_open_attempt_accepts_any_id(self):
        def accept_any(root, fid, attempt):
            return fixstage.attempt_dir(root, fid, attempt)

        with mock.patch.object(fixstage, "_require_open_attempt", accept_any):
            res, open_before, file_before, _ = \
                self._stale_snapshot_scenario(self.inproc)
        self.assertFalse(self.stale_attempt_refused(res, self.repo, open_before,
                                                    file_before))


if __name__ == "__main__":
    unittest.main()
