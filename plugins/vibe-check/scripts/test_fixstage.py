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
import re
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
        # The mutant really used the stale snapshot: it reverted the file.
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotEqual(self.read("f.txt"), file_before)


# Test-side stand-ins for the defects each undo lock guards against.

def _restore_pre_unconditionally(entry, current):
    """The old undo: write the pre bytes back no matter what is there now."""
    return ("restored", entry["pre"])


_REAL_REVERSE = fixstage._reverse_path


def _delete_created_unconditionally(entry, current):
    """Delete a fix-created file even when it changed after the fix wrote it."""
    if entry["pre"] is None:
        return ("restored", None)
    return _REAL_REVERSE(entry, current)


def _undo_from_head(entry, current):
    """Restore from HEAD instead of the pre-edit snapshot."""
    proc = subprocess.run(["git", "show", "HEAD:" + entry["path"]],
                          cwd=entry["root"], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=120)
    if proc.returncode != 0:
        return ("restored", None)
    return ("restored", proc.stdout)


class TestUndo(FixstageCase):
    """begin -> snapshot -> edit -> seal -> [owner action] -> undo."""

    OWNER_5 = "owner edit 5\n"
    FIX_30 = "fixed 30\n"

    def git_state(self):
        head = git(self.repo, "rev-parse", "HEAD").stdout
        cached = git(self.repo, "diff", "--cached").stdout
        index = git(self.repo, "ls-files", "-s").stdout
        return head, cached, index

    def prepare(self, edit, paths=("f.txt",), before=None):
        """Run begin/snapshot, `before()` (owner edit pre-fix), `edit()`, seal."""
        self.set_record(list(paths))
        if before is not None:
            before()
        a = self.begin()
        self.ok("snapshot", a)
        self.pre_bytes = {p: (self.read(p) if os.path.exists(
            os.path.join(self.repo, p)) else None) for p in paths}
        edit()
        self.ok("seal", a)
        return a

    def undo(self, a, runner=None):
        state = self.git_state()
        res = self.sub("undo", a, runner)
        self.assertEqual(self.git_state(), state,
                         "undo moved HEAD or touched the index")
        return res

    def owner_edit_survived(self, repo):
        with open(os.path.join(repo, "f.txt"), "rb") as fh:
            lines = fh.read().decode().splitlines(True)
        return lines[4] == self.OWNER_5 and lines[29] == self.lines[29]

    def created_file_kept(self, repo):
        path = os.path.join(repo, "new.txt")
        if not os.path.exists(path):
            return False
        with open(path, "rb") as fh:
            return fh.read() == b"fix wrote\nowner appended\n"

    # (1) owner edit BEFORE the fix survives; file returns to exact pre bytes
    def _owner_before(self, runner=None):
        a = self.prepare(lambda: self.edit_line("f.txt", 30, self.FIX_30),
                         before=lambda: self.edit_line("f.txt", 5, self.OWNER_5))
        return self.undo(a, runner)

    def test_owner_edit_before_fix_survives(self):
        res = self._owner_before()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.read("f.txt"), self.pre_bytes["f.txt"])
        self.assertTrue(self.owner_edit_survived(self.repo))

    # (2) owner edit AFTER seal (while the check runs) survives
    def _owner_during(self, runner=None):
        a = self.prepare(lambda: self.edit_line("f.txt", 30, self.FIX_30))
        self.edit_line("f.txt", 5, self.OWNER_5)
        return self.undo(a, runner)

    def test_owner_edit_during_check_survives(self):
        res = self._owner_during()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(self.owner_edit_survived(self.repo))
        self.assertNotIn(self.FIX_30.encode(), self.read("f.txt"))

    # (3) owner edits the very line the fix changed -> kept + reported
    def test_conflicting_owner_edit_left_as_is(self):
        a = self.prepare(lambda: self.edit_line("f.txt", 30, self.FIX_30))
        self.edit_line("f.txt", 30, "owner rewrote 30\n")
        before = self.read("f.txt")
        res = self.undo(a)
        self.assertEqual(res.returncode, 3, res.stderr)
        self.assertEqual(res.stdout, "not-undone: f.txt\n")
        self.assertEqual(self.read("f.txt"), before)
        self.assertTrue(os.path.isdir(
            os.path.join(self.sdir(), "closed", a + ".undo-partial")))

    # (4) a created file, unchanged since the fix, is deleted
    def test_created_file_unchanged_is_deleted(self):
        a = self.prepare(lambda: write(self.repo, "new.txt", "fix wrote\n"),
                         paths=("new.txt",))
        res = self.undo(a)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "new.txt")))

    # (5) a created file the owner changed after seal is kept
    def _created_then_owner(self, runner=None):
        a = self.prepare(lambda: write(self.repo, "new.txt", "fix wrote\n"),
                         paths=("new.txt",))
        write(self.repo, "new.txt", "fix wrote\nowner appended\n")
        return self.undo(a, runner)

    def test_created_file_changed_by_owner_is_kept(self):
        res = self._created_then_owner()
        self.assertEqual(res.returncode, 3, res.stderr)
        self.assertEqual(res.stdout, "not-undone: new.txt\n")
        self.assertTrue(self.created_file_kept(self.repo))

    # (6) a tracked file the fix deleted comes back with pre bytes and mode
    def test_deleted_file_restored(self):
        os.chmod(os.path.join(self.repo, "g.txt"), 0o755)
        a = self.prepare(lambda: os.unlink(os.path.join(self.repo, "g.txt")),
                         paths=("g.txt",))
        res = self.undo(a)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.read("g.txt"), b"g\n")
        self.assertEqual(self.mode("g.txt"), 0o755)

    # (6b) the fix deleted a file and the owner recreated it -> kept
    def test_deleted_then_recreated_is_kept(self):
        a = self.prepare(lambda: os.unlink(os.path.join(self.repo, "g.txt")),
                         paths=("g.txt",))
        write(self.repo, "g.txt", "owner's new g\n")
        res = self.undo(a)
        self.assertEqual(res.returncode, 3)
        self.assertEqual(self.read("g.txt"), b"owner's new g\n")

    # (6c) the fix edited a file and the owner deleted it after seal -> kept
    def test_edited_then_deleted_by_owner_is_kept(self):
        a = self.prepare(lambda: self.edit_line("f.txt", 30, self.FIX_30))
        os.unlink(os.path.join(self.repo, "f.txt"))
        res = self.undo(a)
        self.assertEqual(res.returncode, 3, res.stderr)
        self.assertEqual(res.stdout, "not-undone: f.txt\n")
        self.assertFalse(os.path.exists(os.path.join(self.repo, "f.txt")))

    # (7) a mode change by the fix is reversed
    def test_mode_reversed(self):
        os.chmod(os.path.join(self.repo, "f.txt"), 0o644)
        a = self.prepare(lambda: os.chmod(os.path.join(self.repo, "f.txt"),
                                          0o755))
        res = self.undo(a)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.mode("f.txt"), 0o644)

    # (8) HEAD and the index are identical around a multi-path undo
    def test_head_and_index_untouched(self):
        git(self.repo, "add", "--", "g.txt")
        write(self.repo, "staged.txt", "staged\n")
        git(self.repo, "add", "--", "staged.txt")

        def edit():
            self.edit_line("f.txt", 30, self.FIX_30)
            write(self.repo, "g.txt", "fixed g\n")
            write(self.repo, "new.txt", "fix wrote\n")

        a = self.prepare(edit, paths=("f.txt", "g.txt", "new.txt"))
        res = self.undo(a)  # undo() asserts HEAD / --cached / ls-files -s
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.read("f.txt"), self.pre_bytes["f.txt"])
        self.assertEqual(self.read("g.txt"), b"g\n")

    # (9) after undo the attempt is closed
    def test_attempt_closed_after_undo(self):
        a = self.prepare(lambda: self.edit_line("f.txt", 30, self.FIX_30))
        self.assertEqual(self.undo(a).returncode, 0)
        self.assertIsNone(self.open_id())
        self.assertTrue(os.path.isdir(
            os.path.join(self.sdir(), "closed", a + ".undone")))
        res = self.sub("undo", a)
        self.assertEqual(res.returncode, 1)
        self.assertIn(fixstage.REFUSED_STALE, res.stderr)

    # (10) undo on an unsealed attempt is refused and touches nothing
    def test_unsealed_undo_refused(self):
        a = self.begin()
        self.ok("snapshot", a)
        self.edit_line("f.txt", 30, self.FIX_30)
        before = self.read("f.txt")
        res = self.undo(a)
        self.assertEqual(res.returncode, 1)
        self.assertIn("not sealed", res.stderr)
        self.assertEqual(self.read("f.txt"), before)
        self.assertEqual(self.open_id(), a)

    def test_tampered_snapshot_is_not_written(self):
        a = self.prepare(lambda: self.edit_line("f.txt", 30, self.FIX_30))
        write(os.path.join(self.sdir(), a), "0.pre", "attacker bytes\n")
        before = self.read("f.txt")
        res = self.undo(a)
        self.assertEqual(res.returncode, 3)
        self.assertEqual(self.read("f.txt"), before)

    def test_binary_changed_since_seal_is_kept(self):
        write(self.repo, "b.bin", b"\x00\x01\x02 pre\n")
        a = self.prepare(lambda: write(self.repo, "b.bin", b"\x00\x01\x02 post\n"),
                         paths=("b.bin",))
        write(self.repo, "b.bin", b"\x00\x01\x02 owner\n")
        res = self.undo(a)
        self.assertEqual(res.returncode, 3)
        self.assertEqual(self.read("b.bin"), b"\x00\x01\x02 owner\n")

    # ------------------------------------------------------------- mutants

    def test_mutant_m1_unconditional_pre_restore_erases_owner_edit(self):
        with mock.patch.object(fixstage, "_reverse_path",
                               _restore_pre_unconditionally):
            res = self._owner_during(self.inproc)
        self.assertEqual(res.returncode, 0)
        self.assertFalse(self.owner_edit_survived(self.repo))

    def test_mutant_m2_unconditional_delete_loses_owner_bytes(self):
        with mock.patch.object(fixstage, "_reverse_path",
                               _delete_created_unconditionally):
            self._created_then_owner(self.inproc)
        self.assertFalse(self.created_file_kept(self.repo))

    def test_mutant_m3_undo_from_head_erases_pre_fix_owner_edit(self):
        with mock.patch.object(fixstage, "_reverse_path", _undo_from_head):
            res = self._owner_before(self.inproc)
        self.assertEqual(res.returncode, 0)
        self.assertFalse(self.owner_edit_survived(self.repo))


# ---------------------------------------------------------------- commit tests

FIX30 = "line 30 fixed"
OWNER5 = "line 5 owner"


def commit_carries_only(repo, sha, expected_line):
    """True when commit `sha` adds exactly one line, `expected_line`."""
    out = git(repo, "show", "--format=", "--unified=0", sha).stdout
    added = [line[1:] for line in out.splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    return added == [expected_line]


def _swept_commit(repo, path):
    """The 999.15 defect: `git add` + a pathspec commit of the whole file."""
    git(repo, "add", "--", path)
    git(repo, "commit", "-q", "-m", "swept", "--", path)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def _post_from_working_tree(root, adir, entry):
    """Mutant: read the 'post' bytes from the working tree, not the seal."""
    with open(os.path.join(root, entry["path"]), "rb") as fh:
        return fh.read()


class CommitCase(FixstageCase):
    """Commit helpers: a full begin -> snapshot -> edit -> seal -> commit flow."""

    def rev(self, name="HEAD"):
        return git(self.repo, "rev-parse", name).stdout.strip()

    def index_state(self):
        return git(self.repo, "ls-files", "-s").stdout

    def fix_flow(self, edits, owner_after_seal=None, runner=None, paths=None):
        if paths is not None:
            self.set_record(list(paths))
        attempt = self.begin()
        self.ok("snapshot", attempt)
        edits()
        self.ok("seal", attempt)
        if owner_after_seal is not None:
            owner_after_seal()
        return self.sub("commit", attempt, runner), attempt

    def sha_of(self, res):
        for line in res.stdout.splitlines():
            if line.startswith("commit_sha="):
                return line[len("commit_sha="):]
        self.fail("no commit_sha in %r" % res.stdout)

    def closed_outcome(self, attempt):
        closed = os.path.join(self.sdir(), "closed")
        if not os.path.isdir(closed):
            return None
        for name in os.listdir(closed):
            if name.startswith(attempt + "."):
                return name[len(attempt) + 1:]
        return None

    def fix30(self):
        self.edit_line("f.txt", 30, FIX30 + "\n")

    def owner5(self):
        self.edit_line("f.txt", 5, OWNER5 + "\n")

    def committed_text(self, rev, path="f.txt"):
        return git(self.repo, "show", "%s:%s" % (rev, path)).stdout


class TestCommit(CommitCase):

    def test_a_owner_unstaged_edit_stays_out(self):
        self.owner5()
        pre = self.rev()
        res, _ = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        sha = self.sha_of(res)
        self.assertEqual(sha, self.rev())
        self.assertEqual(self.rev("HEAD^"), pre)
        stat = git(self.repo, "show", "--format=", "--name-only", sha).stdout
        self.assertEqual(stat.split(), ["f.txt"])
        self.assertTrue(commit_carries_only(self.repo, sha, FIX30))
        self.assertIn(OWNER5, self.read("f.txt").decode())
        self.assertEqual(git(self.repo, "diff", "--cached").stdout, "")
        self.assertFalse(os.path.exists(
            os.path.join(self.repo, ".git", "index.lock")))
        reflog = git(self.repo, "reflog", "show", "--format=%gs", "-n1",
                     "refs/heads/main").stdout
        self.assertTrue(reflog.startswith("commit: "), reflog)

    def test_a3_failure_after_publish_reports_the_commit(self):
        # Anything that fails once the ref is published must report the
        # published sha (exit 0, staging left as is), never `refused` exit 1.
        def boom(*a, **k):
            raise OSError("SENTINEL_after_publish")
        for seam in ("_sync_real_index", "_commit_tree_of", "_run_post_commit"):
            with self.subTest(seam=seam):
                self.setUp_fresh()
                pre = self.rev()
                with mock.patch.object(fixstage, seam, boom):
                    res, attempt = self.fix_flow(self.fix30, runner=self.inproc)
                self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
                sha = self.sha_of(res)
                self.assertEqual(sha, self.rev())
                self.assertEqual(self.rev("HEAD^"), pre)
                self.assertIn("index-left-as-is: f.txt", res.stdout)
                self.assertIn("after the commit was published", res.stderr)
                self.assertNotIn("SENTINEL", res.stderr)
                # `committed` removes the attempt dir; a refusal would leave
                # closed/<attempt>.refused behind.
                self.assertIsNone(self.closed_outcome(attempt))
                self.assertIsNone(self.open_id())

    def setUp_fresh(self):
        self.tearDown()
        self.setUp()

    def _a2(self, runner=None):
        return self.fix_flow(
            self.fix30,
            owner_after_seal=lambda: self.edit_line("f.txt", 12, "line 12 owner\n"),
            runner=runner)

    def test_a2_owner_edit_after_seal_stays_out(self):
        res, _ = self._a2()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(commit_carries_only(self.repo, self.sha_of(res), FIX30))
        self.assertIn("line 12 owner", self.read("f.txt").decode())

    def test_b_foreign_staged_file_stays_staged(self):
        write(self.repo, "g.txt", "g staged\n")
        git(self.repo, "add", "--", "g.txt")
        staged = git(self.repo, "ls-files", "-s", "--", "g.txt").stdout
        res, _ = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        sha = self.sha_of(res)
        self.assertEqual(git(self.repo, "ls-files", "-s", "--", "g.txt").stdout,
                         staged)
        names = git(self.repo, "show", "--format=", "--name-only", sha).stdout
        self.assertNotIn("g.txt", names.split())
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only").stdout
                         .split(), ["g.txt"])

    def test_c_two_fixes_same_file_two_commits(self):
        res1, _ = self.fix_flow(self.fix30)
        self.assertEqual(res1.returncode, 0, res1.stdout + res1.stderr)
        res2, _ = self.fix_flow(
            lambda: self.edit_line("f.txt", 10, "line 10 fixed\n"))
        self.assertEqual(res2.returncode, 0, res2.stdout + res2.stderr)
        sha1, sha2 = self.sha_of(res1), self.sha_of(res2)
        self.assertNotEqual(sha1, sha2)
        self.assertEqual(self.rev("HEAD^"), sha1)
        self.assertTrue(commit_carries_only(self.repo, sha1, FIX30))
        self.assertTrue(commit_carries_only(self.repo, sha2, "line 10 fixed"))

    def test_g_created_file_modes(self):
        for name, perm, mode in (("new.txt", 0o644, "100644"),
                                 ("new.sh", 0o755, "100755")):
            with self.subTest(name=name):
                def create():
                    write(self.repo, name, "created\n")
                    os.chmod(os.path.join(self.repo, name), perm)
                res, _ = self.fix_flow(create, paths=[name])
                self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
                entry = git(self.repo, "ls-tree", self.sha_of(res), "--",
                            name).stdout
                self.assertTrue(entry.startswith(mode + " "), entry)
                self.assertEqual(git(self.repo, "diff", "--cached").stdout, "")

    def test_g2_attempt_closed_after_commit(self):
        res, attempt = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIsNone(self.open_id())
        self.assertFalse(os.path.exists(os.path.join(self.sdir(), attempt)))
        again = self.sub("commit", attempt)
        self.assertEqual(again.returncode, 1)
        self.assertIn("stale", again.stderr)

    def test_g3_busy_index_lock_left_alone(self):
        lock = os.path.join(self.repo, ".git", "index.lock")

        def take_lock():
            with open(lock, "wb") as fh:
                fh.write(b"another process\n")
        try:
            res, _ = self.fix_flow(self.fix30, owner_after_seal=take_lock)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertIn("index-left-as-is: f.txt", res.stdout.splitlines())
            with open(lock, "rb") as fh:
                self.assertEqual(fh.read(), b"another process\n")
        finally:
            if os.path.exists(lock):
                os.unlink(lock)

    def test_g4_unborn_repo(self):
        self.repo = gitfixture.make_repo(os.path.join(self.tmp, "unborn"))
        res, _ = self.fix_flow(lambda: write(self.repo, "new.txt", "first\n"),
                               paths=["new.txt"])
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        sha = self.sha_of(res)
        self.assertEqual(self.rev("main"), sha)
        parents = git(self.repo, "rev-list", "--parents", "-n1", sha).stdout
        self.assertEqual(parents.split(), [sha])
        self.assertEqual(git(self.repo, "symbolic-ref", "HEAD").stdout.strip(),
                         "refs/heads/main")

    # ------------------------------------------------------------- mutants

    def test_l_swept_commit_is_detected(self):
        self.owner5()
        self.fix30()
        sha = _swept_commit(self.repo, "f.txt")
        self.assertFalse(commit_carries_only(self.repo, sha, FIX30))

    # ------------------------------------------------- D-02 not separable

    def head_unchanged(self, repo, pre):
        return git(repo, "rev-parse", "HEAD").stdout.strip() == pre

    def _d(self, runner=None):
        self.owner5()
        pre = self.rev()
        index = self.index_state()
        res, attempt = self.fix_flow(
            lambda: self.edit_line("f.txt", 6, "line 6 fixed\n"), runner=runner)
        return res, attempt, pre, index

    def test_d_overlap_not_separable(self):
        res, attempt, pre, index = self._d()
        self.assertEqual(res.returncode, 3, res.stdout + res.stderr)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: the fix overlaps uncommitted edits")
        self.assertTrue(self.head_unchanged(self.repo, pre))
        text = self.read("f.txt").decode()
        self.assertIn(OWNER5, text)
        self.assertIn("line 6 fixed", text)
        self.assertEqual(self.index_state(), index)
        self.assertIsNone(self.open_id())
        self.assertEqual(self.closed_outcome(attempt), "not-separable")

    def test_d_mutant_conflict_ignored_moves_head(self):
        with mock.patch.object(fixstage, "_merge_rc_is_conflict",
                               lambda rc: False):
            res, _, pre, _ = self._d(self.inproc)
        self.assertFalse(self.head_unchanged(self.repo, pre))

    def test_e_untracked_file(self):
        write(self.repo, "u.txt", "mine\n")
        pre = self.rev()
        res, attempt = self.fix_flow(lambda: write(self.repo, "u.txt", "fixed\n"),
                                     paths=["u.txt"])
        self.assertEqual(res.returncode, 3)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: file was untracked before the fix")
        self.assertEqual(self.rev(), pre)
        self.assertEqual(self.read("u.txt"), b"fixed\n")
        self.assertEqual(self.closed_outcome(attempt), "not-separable")

    def test_f_symlink_in_last_commit(self):
        os.symlink("f.txt", os.path.join(self.repo, "s.txt"))
        git(self.repo, "add", "--", "s.txt")
        git(self.repo, "commit", "-q", "-m", "link")
        os.unlink(os.path.join(self.repo, "s.txt"))
        write(self.repo, "s.txt", "now a file\n")
        pre = self.rev()
        res, _ = self.fix_flow(lambda: write(self.repo, "s.txt", "fixed\n"),
                               paths=["s.txt"])
        self.assertEqual(res.returncode, 3)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: symlink or submodule")
        self.assertEqual(self.rev(), pre)

    def test_f2_binary_file(self):
        write(self.repo, "b.bin", b"\x00\x01 one\n")
        git(self.repo, "add", "--", "b.bin")
        git(self.repo, "commit", "-q", "-m", "bin")
        pre = self.rev()
        res, _ = self.fix_flow(lambda: write(self.repo, "b.bin", b"\x00\x01 two\n"),
                               paths=["b.bin"])
        self.assertEqual(res.returncode, 3)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: binary or unmergeable file")
        self.assertEqual(self.rev(), pre)
        self.assertEqual(self.read("b.bin"), b"\x00\x01 two\n")

    def test_h_owner_staged_same_file(self):
        self.owner5()
        git(self.repo, "add", "--", "f.txt")
        res, _ = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(commit_carries_only(self.repo, self.sha_of(res), FIX30))
        staged = git(self.repo, "diff", "--cached", "--unified=0").stdout
        added = [l[1:] for l in staged.splitlines()
                 if l.startswith("+") and not l.startswith("+++")]
        self.assertEqual(added, [OWNER5])
        self.assertEqual(git(self.repo, "diff").stdout, "")

    def test_j_sc5_handoff(self):
        pre = self.rev()
        branch = git(self.repo, "symbolic-ref", "HEAD").stdout.strip()
        # an exit 3 leaves HEAD where it was
        self.owner5()
        res, _ = self.fix_flow(lambda: self.edit_line("f.txt", 6, "line 6 fixed\n"))
        self.assertEqual(res.returncode, 3)
        self.assertEqual(self.rev(), pre)
        # an undo leaves HEAD where it was
        attempt = self.begin()
        self.ok("snapshot", attempt)
        self.edit_line("f.txt", 20, "line 20 tried\n")
        self.ok("seal", attempt)
        self.ok("undo", attempt)
        self.assertEqual(self.rev(), pre)
        # an applied commit is the new HEAD, child of the pre-fix HEAD
        res, _ = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        sha = self.sha_of(res)
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertEqual(sha, self.rev())
        self.assertEqual(self.rev("HEAD^"), pre)
        self.assertEqual(git(self.repo, "symbolic-ref", "HEAD").stdout.strip(),
                         branch)

    def test_k_hostile_title_refused(self):
        self.set_record(["f.txt"], title="$(touch pwned)")
        pre = self.rev()
        res, attempt = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 1)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "pwned")))
        self.assertFalse(os.path.exists("pwned"))
        self.assertEqual(self.rev(), pre)
        self.assertEqual(self.closed_outcome(attempt), "refused")

    def test_l2_mutant_post_from_working_tree_sweeps_owner_edit(self):
        with mock.patch.object(fixstage, "_post_bytes", _post_from_working_tree):
            res, _ = self._a2(self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(commit_carries_only(self.repo, self.sha_of(res), FIX30))



def base_content_kept(repo, path, data):
    proc = git(repo, "show", "main:" + path, check=False)
    return proc.returncode == 0 and proc.stdout.encode() == data


def base_mode_kept(repo, path, mode):
    entry = git(repo, "ls-tree", "main", "--", path).stdout
    return entry.startswith(mode + " ")


def _other_terminal_commit(repo, message):
    """Commit what is in the real index, hooks off, working tree untouched."""
    git(repo, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


class TestBasePrecondition(CommitCase):
    """An owner commit between seal and BASE capture is never overwritten."""

    def blob(self, data):
        src = os.path.join(self.tmp, "blobsrc")
        with open(src, "wb") as fh:
            fh.write(data)
        return git(self.repo, "hash-object", "-w", "--", src).stdout.strip()

    def stage_new_owner_file(self):
        git(self.repo, "update-index", "--add", "--cacheinfo",
            "100644,%s,new.txt" % self.blob(b"owner\n"))

    def _t(self, runner=None):
        state = {}

        def owner():
            self.stage_new_owner_file()
            state["owner"] = _other_terminal_commit(self.repo, "owner")
            state["index"] = self.index_state()
        res, attempt = self.fix_flow(lambda: write(self.repo, "new.txt", "fix\n"),
                                     owner_after_seal=owner, runner=runner,
                                     paths=["new.txt"])
        return res, attempt, state

    def test_t_created_path_committed_by_owner(self):
        with mock.patch.object(fixstage, "_build_temp_index",
                               side_effect=AssertionError("temp index built")) as rec:
            res, attempt, state = self._t(self.inproc)
        self.assertFalse(rec.called)
        self.assertEqual(res.returncode, 3, res.stdout + res.stderr)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: the file now exists in the last commit")
        self.assertEqual(self.rev("main"), state["owner"])
        self.assertTrue(base_content_kept(self.repo, "new.txt", b"owner\n"))
        self.assertEqual(self.read("new.txt"), b"fix\n")
        self.assertEqual(self.index_state(), state["index"])
        self.assertEqual(self.closed_outcome(attempt), "not-separable")
        closed = os.path.join(self.sdir(), "closed", attempt + ".not-separable")
        self.assertFalse(os.path.exists(os.path.join(closed, "msg")))
        self.assertFalse(os.path.exists(os.path.join(closed, "tmp-index")))

    def test_t_mutant_no_base_check_overwrites_owner_commit(self):
        with mock.patch.object(fixstage, "_base_precondition",
                               lambda entry, base_entry, real_entry: None):
            res, _, _ = self._t(self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(base_content_kept(self.repo, "new.txt", b"owner\n"))

    def test_t1_created_path_staged_by_owner(self):
        pre = self.rev()
        res, _ = self.fix_flow(lambda: write(self.repo, "new.txt", "fix\n"),
                               owner_after_seal=self.stage_new_owner_file,
                               paths=["new.txt"])
        self.assertEqual(res.returncode, 3)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: the file is staged in your index")
        self.assertEqual(self.rev(), pre)

    def test_t2_tracked_path_deleted_by_owner_commit(self):
        def owner():
            git(self.repo, "rm", "--cached", "-q", "--", "f.txt")
            _other_terminal_commit(self.repo, "delete f")
        res, _ = self.fix_flow(self.fix30, owner_after_seal=owner)
        self.assertEqual(res.returncode, 3)
        self.assertEqual(res.stdout.strip(),
                         "not-separable: the file is no longer in the last commit")
        self.assertEqual(git(self.repo, "ls-tree", "main", "--", "f.txt").stdout,
                         "")
        self.assertIn(FIX30, self.read("f.txt").decode())

    def _t3(self, runner=None):
        def owner():
            # Mode only: `update-index --chmod=+x <path>` would also re-stage
            # the working-tree bytes (the fix), so set the entry directly.
            oid = git(self.repo, "rev-parse", "HEAD:f.txt").stdout.strip()
            git(self.repo, "update-index", "--cacheinfo",
                "100755,%s,f.txt" % oid)
            _other_terminal_commit(self.repo, "chmod")
        return self.fix_flow(self.fix30, owner_after_seal=owner, runner=runner)

    def test_t3_owner_committed_mode_kept(self):
        res, _ = self._t3()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(base_mode_kept(self.repo, "f.txt", "100755"))
        self.assertNotIn(FIX30, self.committed_text("main^"))
        self.assertTrue(commit_carries_only(self.repo, self.sha_of(res), FIX30))

    def test_t3_mutant_post_mode_reverts_owner_chmod(self):
        with mock.patch.object(
                fixstage, "_target_mode",
                lambda entry, base_entry: fixstage._git_mode(entry["post_mode"])):
            res, _ = self._t3(self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(base_mode_kept(self.repo, "f.txt", "100755"))

    def test_t4_owner_committed_content_kept(self):
        state = {}

        def owner():
            lines = self.committed_text("HEAD").splitlines(True)
            lines[4] = OWNER5 + "\n"
            git(self.repo, "update-index", "--cacheinfo",
                "100644,%s,f.txt" % self.blob("".join(lines).encode()))
            state["owner"] = _other_terminal_commit(self.repo, "line 5")
        res, _ = self.fix_flow(self.fix30, owner_after_seal=owner)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        sha = self.sha_of(res)
        self.assertEqual(self.rev(sha + "^"), state["owner"])
        text = self.committed_text("main")
        self.assertIn(OWNER5, text)
        self.assertIn(FIX30, text)


def _unsigned_commit_object(root, tree, base, msgfile):
    """Mutant: commit-tree that ignores commit.gpgSign."""
    proc = fixstage._git(root, "commit-tree", "-p", base, "-F", msgfile, tree)
    return proc.stdout.strip() if proc.returncode == 0 else None


class HookCase(CommitCase):

    def hook(self, name, body):
        path = os.path.join(self.repo, ".git", "hooks", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("#!/bin/sh\n" + body + "\n")
        os.chmod(path, 0o755)
        return path


class TestCommitRejected(HookCase):

    def assert_rejected(self, res, attempt, pre):
        self.assertEqual(res.returncode, 4, res.stdout + res.stderr)
        self.assertTrue(res.stdout.startswith("commit-not-created:"), res.stdout)
        self.assertEqual(self.rev(), pre)
        self.assertIn(FIX30, self.read("f.txt").decode())
        self.assertEqual(self.closed_outcome(attempt), "hook-rejected")

    def test_i_pre_commit_rejects(self):
        self.hook("pre-commit", "echo nope from hook\nexit 1")
        pre = self.rev()
        res, attempt = self.fix_flow(self.fix30)
        self.assert_rejected(res, attempt, pre)
        self.assertIn("your commit hook rejected the commit", res.stdout)
        self.assertIn("nope from hook", res.stdout)

    def test_i2_commit_msg_rejects(self):
        self.hook("commit-msg", "exit 1")
        pre = self.rev()
        res, attempt = self.fix_flow(self.fix30)
        self.assert_rejected(res, attempt, pre)

    def marker(self):
        return os.path.join(self.tmp, "hookmark")

    def hooks_ran(self, repo):
        return os.path.exists(self.marker())

    def _i3(self, runner=None):
        self.hook("pre-commit",
                  'printf "%%s\\n%%s\\n" "$GIT_INDEX_FILE" "$PWD" > "%s"'
                  % self.marker())
        self.hook("commit-msg", 'cp "$1" "%s"'
                  % os.path.join(self.tmp, "msgcopy"))
        return self.fix_flow(self.fix30, runner=runner)

    def test_i3_hooks_see_temp_index_and_message(self):
        res, _ = self._i3()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(self.hooks_ran(self.repo))
        with open(self.marker()) as fh:
            index_file, pwd = fh.read().splitlines()
        self.assertNotEqual(os.path.realpath(index_file),
                            os.path.join(self.repo, ".git", "index"))
        self.assertTrue(index_file.endswith("tmp-index"), index_file)
        self.assertEqual(os.path.realpath(pwd), self.repo)
        with open(os.path.join(self.tmp, "msgcopy")) as fh:
            self.assertEqual(fh.read(), "fix(review-pass-1): Fix it\n")

    def test_i3_mutant_hooks_skipped(self):
        with mock.patch.object(fixstage, "_run_commit_hooks",
                               lambda root, temp_index, msgfile: (True, "")):
            res, _ = self._i3(self.inproc)
        self.assertEqual(res.returncode, 0)
        self.assertFalse(self.hooks_ran(self.repo))

    def signing_respected(self, repo, rc):
        if rc != 0:
            return True
        raw = git(repo, "cat-file", "commit", "HEAD").stdout
        return "\ngpgsig " in raw

    def _i4(self, runner=None):
        gpg = os.path.join(self.tmp, "fake-gpg")
        with open(gpg, "w") as fh:
            fh.write("#!/bin/sh\nexit 1\n")
        os.chmod(gpg, 0o755)
        git(self.repo, "config", "commit.gpgSign", "true")
        git(self.repo, "config", "gpg.program", gpg)
        return self.fix_flow(self.fix30, runner=runner)

    def test_i4_signing_failure(self):
        pre = self.rev()
        res, attempt = self._i4()
        self.assert_rejected(res, attempt, pre)
        self.assertEqual(res.stdout.splitlines()[0],
                         "commit-not-created: the commit could not be signed")
        self.assertTrue(self.signing_respected(self.repo, res.returncode))

    def test_i4_mutant_unsigned_commit(self):
        with mock.patch.object(fixstage, "_make_commit_object",
                               _unsigned_commit_object):
            res, _ = self._i4(self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(self.signing_respected(self.repo, res.returncode))


class TestRetry(HookCase):

    def _rejected_then_owner_edit(self):
        hook = self.hook("pre-commit", "exit 1")
        res, attempt_a = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 4, res.stdout + res.stderr)
        self.owner5()
        return hook, attempt_a

    def test_r_retry_never_reuses_stale_attempt(self):
        hook, a = self._rejected_then_owner_edit()
        before = self.read("f.txt")
        for name in ("undo", "commit"):
            res = self.sub(name, a)
            self.assertEqual(res.returncode, 1, name)
            self.assertEqual(self.read("f.txt"), before)
        self.assertTrue(os.path.isdir(
            os.path.join(self.sdir(), "closed", a + ".hook-rejected")))
        self.assertIsNone(self.open_id())
        os.unlink(hook)
        b = self.begin()
        self.assertNotEqual(a, b)
        self.ok("snapshot", b)
        with open(os.path.join(self.sdir(), b, "0.pre"), "rb") as fh:
            self.assertEqual(fh.read(), before)
        self.edit_line("f.txt", 20, "line 20 fixed\n")
        self.ok("seal", b)
        res = self.sub("commit", b)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(commit_carries_only(self.repo, self.sha_of(res),
                                            "line 20 fixed"))
        text = self.read("f.txt").decode()
        self.assertIn(OWNER5, text)
        self.assertIn(FIX30, text)

    def test_r_mutant_stale_attempt_accepted(self):
        hook, a = self._rejected_then_owner_edit()
        os.unlink(hook)
        b = self.begin()
        self.ok("snapshot", b)
        self.edit_line("f.txt", 20, "line 20 fixed\n")
        self.ok("seal", b)
        original = fixstage._require_open_attempt

        def accept_closed(root, fid, attempt):
            closed = os.path.join(fixstage.stage_dir(root, fid), "closed")
            for name in os.listdir(closed):
                if name.startswith(attempt + "."):
                    return os.path.join(closed, name)
            return original(root, fid, attempt)
        with mock.patch.object(fixstage, "_require_open_attempt", accept_closed):
            res = self.sub("commit", a, self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(commit_carries_only(self.repo, self.sha_of(res),
                                             "line 20 fixed"))



# ------------------------------------------------- BASE binding (pass-3 f1)

RACE_LABELS = ("after-base", "after-read-tree", "after-hooks", "in-publish")
OTHER_CHANGED = "other changed\n"


def _env_without_index():
    env = gitfixture.helper_env()
    env.pop("GIT_INDEX_FILE", None)
    return env


def foreign_commit(repo):
    """Another terminal commits other.txt (hooks off, real index)."""
    write(repo, "other.txt", OTHER_CHANGED)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "commit", "-q",
                    "-m", "other-terminal", "--", "other.txt"],
                   cwd=repo, env=_env_without_index(), check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def foreign_change_kept(repo):
    proc = git(repo, "show", "main:other.txt", check=False)
    return proc.returncode == 0 and proc.stdout == OTHER_CHANGED


def foreign_commit_kept(repo, sha):
    return git(repo, "merge-base", "--is-ancestor", sha, "main",
               check=False).returncode == 0


def _late_parent_commit_object(root, tree, base, msgfile):
    """Mutant: parent = HEAD read at commit time (git commit's late capture)."""
    head = fixstage._git(root, "rev-parse", "HEAD").stdout.strip()
    proc = fixstage._git(root, "commit-tree", "-p", head, "-F", msgfile, tree)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _late_base_publish(root, base, base_symref, new, subject):
    """Mutant: compare-and-swap against the CURRENT HEAD instead of BASE."""
    fixstage._race_point(root, "in-publish")
    head = fixstage._git(root, "rev-parse", "HEAD").stdout.strip()
    return fixstage._git(root, "update-ref", base_symref, new,
                         head).returncode == 0


def _publish_without_cas(root, base, base_symref, new, subject):
    """Mutant: no pre-check and no old value - a forced move."""
    fixstage._race_point(root, "in-publish")
    return fixstage._git(root, "update-ref", base_symref, new).returncode == 0


FORBIDDEN_REF_TOKENS = ('"-d"', "--delete", '"reset"', "branch -f",
                        '"branch", "-f"', "--stdin")


def ref_writes_forward_only(text):
    """Source lock: exactly one ref write, inside _publish_ref, with the
    old value as its last argument, and no deleting/forcing/rewinding form."""
    code = "\n".join(line for line in text.splitlines()
                     if not line.strip().startswith("#"))
    if code.count("update-ref") != 1:
        return False
    if any(token in code for token in FORBIDDEN_REF_TOKENS):
        return False
    at = code.index("update-ref")
    func_start = code.rfind("\ndef ", 0, at)
    if func_start < 0 or not code.startswith("\ndef _publish_ref(", func_start):
        return False
    call_start = code.rfind("_git(", 0, at)
    if call_start < func_start:
        return False
    depth = 0
    for end in range(call_start + len("_git"), len(code)):
        if code[end] == "(":
            depth += 1
        elif code[end] == ")":
            depth -= 1
            if depth == 0:
                break
    call = code[call_start:end + 1]
    body = code[func_start:call_start]
    return (re.search(r",\s*old\s*\)$", call) is not None
            and re.search(r"\bold = base\b", body) is not None)


class TestBaseBinding(CommitCase):

    def setUp(self):
        CommitCase.setUp(self)
        write(self.repo, "other.txt", "other\n")
        git(self.repo, "add", "--", "other.txt")
        git(self.repo, "commit", "-q", "-m", "other")

    def racer(self, wanted, state):
        def race(root, label):
            if label == wanted and "sha" not in state:
                state["sha"] = foreign_commit(self.repo)
        return race

    def run_race(self, wanted, patches=()):
        state = {}
        pre = self.rev()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(
                fixstage, "_race_point", self.racer(wanted, state)))
            for name, value in patches:
                stack.enter_context(mock.patch.object(fixstage, name, value))
            res, attempt = self.fix_flow(self.fix30, runner=self.inproc)
        return res, attempt, state, pre

    def test_s_foreign_commit_at_every_race_point(self):
        for label in RACE_LABELS:
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                res, attempt, state, pre = self.run_race(label)
                self.assertEqual(res.returncode, 6, res.stdout + res.stderr)
                self.assertTrue(res.stdout.startswith("head-moved:"), res.stdout)
                self.assertEqual(self.rev("main"), state["sha"])
                self.assertEqual(self.rev(state["sha"] + "^"), pre)
                self.assertTrue(foreign_change_kept(self.repo))
                self.assertEqual(git(self.repo, "log", "-S", FIX30,
                                     "--format=%H", "main").stdout, "")
                self.assertIn(FIX30, self.read("f.txt").decode())
                self.assertEqual(self.closed_outcome(attempt), "head-moved")

    def test_s_mutant_late_parent_reverts_foreign_change(self):
        res, _, state, _ = self.run_race(
            "after-read-tree",
            patches=(("_make_commit_object", _late_parent_commit_object),
                     ("_publish_ref", _late_base_publish)))
        self.assertIn("sha", state)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(foreign_change_kept(self.repo))

    def test_s_mutant_no_cas_drops_foreign_commit(self):
        res, _, state, _ = self.run_race(
            "in-publish", patches=(("_publish_ref", _publish_without_cas),))
        self.assertIn("sha", state)
        self.assertFalse(foreign_commit_kept(self.repo, state["sha"]))

    def source(self):
        with open(os.path.join(SCRIPTS_DIR, "fixstage.py")) as fh:
            return fh.read()

    def test_ref_writes_forward_only(self):
        self.assertTrue(ref_writes_forward_only(self.source()))

    def test_ref_lock_mutants(self):
        text = self.source()
        call = '"update-ref", "-m", "commit: " + subject, *target,\n                new, old)'
        self.assertIn(call, text)
        mutants = {
            "second write": text + '\nX = ["git", "update-ref", ref, new]\n',
            "delete form": text.replace('"update-ref", "-m"',
                                        '"update-ref", "-d", "-m"'),
            "no old value": text.replace(call, call.replace(
                "new, old)", "new)")),
        }
        for name, mutated in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(mutated, text)
                self.assertFalse(ref_writes_forward_only(mutated))


class TestCommitHooks(HookCase):

    def _m(self, runner=None):
        self.owner5()
        self.hook("pre-commit", "git add f.txt")
        return self.fix_flow(self.fix30, runner=runner)

    def test_m_hook_changed_content_reported(self):
        pre = self.rev()
        res, attempt = self._m()
        self.assertEqual(res.returncode, 5, res.stdout + res.stderr)
        self.assertNotIn("commit_sha=", res.stdout)
        first = res.stdout.splitlines()[0]
        self.assertTrue(first.startswith("hook-changed: "), res.stdout)
        sha = first[len("hook-changed: "):]
        self.assertEqual(self.rev("main"), sha)
        self.assertEqual(self.rev(sha + "^"), pre)
        self.assertEqual(git(self.repo, "diff", "--cached", "--", "f.txt").stdout,
                         "")
        text = self.read("f.txt").decode()
        self.assertIn(OWNER5, text)
        self.assertIn(FIX30, text)
        self.assertEqual(self.closed_outcome(attempt), "hook-changed")

    def test_m_mutant_tree_check_skipped_claims_success(self):
        with mock.patch.object(fixstage, "_tree_matches", lambda a, b: True):
            res, _ = self._m(self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(commit_carries_only(self.repo, self.sha_of(res), FIX30))

    def test_o_post_commit_moves_head(self):
        mark = os.path.join(self.tmp, "post-mark")
        self.hook("post-commit",
                  '[ -f "%s" ] && exit 0\ntouch "%s"\n'
                  'git commit -q --allow-empty -m extra' % (mark, mark))
        pre = self.rev()
        index = self.index_state()
        res, attempt = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 7, res.stdout + res.stderr)
        first = res.stdout.splitlines()[0]
        self.assertTrue(first.startswith("moved-after-commit: "), res.stdout)
        sha = first[len("moved-after-commit: "):]
        self.assertNotIn("commit_sha=", res.stdout)
        self.assertEqual(self.rev("HEAD^"), sha)
        self.assertEqual(self.rev(sha + "^"), pre)
        self.assertEqual(self.index_state(), index)
        self.assertEqual(self.closed_outcome(attempt), "moved-after-commit")

    def _foreign_from_hook(self, final):
        mark = os.path.join(self.tmp, "pre-mark")
        self.hook("pre-commit",
                  '[ -f "%s" ] && exit 0\ntouch "%s"\n'
                  'env -u GIT_INDEX_FILE git commit -q --allow-empty '
                  '-m other-terminal\nexit %d' % (mark, mark, final))
        pre = self.rev()
        index = self.index_state()
        res, attempt = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 6, res.stdout + res.stderr)
        self.assertTrue(res.stdout.startswith("head-moved:"), res.stdout)
        main = self.rev("main")
        self.assertNotEqual(main, pre)
        self.assertEqual(self.rev(main + "^"), pre)
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s", "main")
                         .stdout.strip(), "other-terminal")
        self.assertIn(FIX30, self.read("f.txt").decode())
        self.assertEqual(self.index_state(), index)
        self.assertEqual(self.closed_outcome(attempt), "head-moved")

    def test_p_foreign_commit_from_failing_hook(self):
        self._foreign_from_hook(1)

    def test_p2_foreign_commit_from_passing_hook(self):
        self._foreign_from_hook(0)


def real_index_entry_is(repo, path, mode, oid):
    entry = git(repo, "ls-files", "-s", "--", path).stdout.split()
    return entry[:2] == [mode, oid]


def _sync_check_then_write(root, before, targets, workdir):
    """Mutant: compare, then write the real index with no lock held."""
    paths = sorted(targets)
    now = fixstage._read_index_entries(root, None, paths)
    ok = [p for p in paths if fixstage._entry_equal(now.get(p), before.get(p))]
    fixstage._between_compare_and_publish(root)
    for path in ok:
        mode, oid = targets[path]
        fixstage._git(root, "update-index", "--cacheinfo",
                      "%s,%s,%s" % (mode, oid, path))
    return [p for p in paths if p not in ok]


class TestIndexSync(HookCase):

    def entry(self, path="f.txt"):
        return git(self.repo, "ls-files", "-s", "--", path).stdout.split()[:2]

    def test_n_hook_changed_real_entry_left(self):
        src = os.path.join(self.tmp, "variant")
        with open(src, "w") as fh:
            fh.write("variant\n")
        variant = git(self.repo, "hash-object", "-w", "--", src).stdout.strip()
        self.hook("pre-commit", "env -u GIT_INDEX_FILE git update-index "
                  "--cacheinfo 100644,%s,f.txt" % variant)
        res, _ = self.fix_flow(self.fix30)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("index-left-as-is: f.txt", res.stdout.splitlines())
        self.assertEqual(self.entry(), ["100644", variant])

    def _n2(self, runner=None):
        oid = self.entry()[1]
        # Mode only, same oid (`--chmod=+x <path>` would re-stage the file).
        self.hook("pre-commit", "env -u GIT_INDEX_FILE git update-index "
                  "--cacheinfo 100755,%s,f.txt" % oid)
        res, _ = self.fix_flow(self.fix30, runner=runner)
        return res, oid

    def test_n2_mode_only_change_left(self):
        res, oid = self._n2()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("index-left-as-is: f.txt", res.stdout.splitlines())
        self.assertTrue(real_index_entry_is(self.repo, "f.txt", "100755", oid))

    def test_n2_mutant_oid_only_compare_loses_chmod(self):
        def oid_only(a, b):
            return (a and a[1]) == (b and b[1])
        with mock.patch.object(fixstage, "_entry_equal", oid_only):
            res, oid = self._n2(self.inproc)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertFalse(real_index_entry_is(self.repo, "f.txt", "100755", oid))

    def no_lost_update(self, repo, attempts):
        for name, rc in attempts:
            if rc != 0:
                continue
            if name == "chmod" and self.entry("f.txt")[0] != "100755":
                return False
            if name == "add":
                want = git(repo, "hash-object", "--", "g.txt").stdout.strip()
                if self.entry("g.txt")[1] != want:
                    return False
        return True

    def _q(self, patches=()):
        attempts = []
        stderr = []

        def concurrent(root):
            for name, argv in (("chmod", ["update-index", "--chmod=+x", "--",
                                          "f.txt"]),
                               ("add", ["add", "--", "g.txt"])):
                proc = subprocess.run(["git"] + argv, cwd=self.repo,
                                      env=_env_without_index(),
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True,
                                      timeout=120)
                attempts.append((name, proc.returncode))
                stderr.append(proc.stderr)
        write(self.repo, "g.txt", "g changed\n")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(
                fixstage, "_between_compare_and_publish", concurrent))
            for name, value in patches:
                stack.enter_context(mock.patch.object(fixstage, name, value))
            res, _ = self.fix_flow(self.fix30, runner=self.inproc)
        return res, attempts, stderr

    def test_q_lock_window_refuses_concurrent_writers(self):
        res, attempts, stderr = self._q()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual([rc != 0 for _, rc in attempts], [True, True])
        for err in stderr:
            self.assertIn("index.lock", err)
        self.assertTrue(self.no_lost_update(self.repo, attempts))
        self.assertFalse(os.path.exists(
            os.path.join(self.repo, ".git", "index.lock")))

    def test_q_mutant_unlocked_sync_loses_update(self):
        res, attempts, _ = self._q(
            patches=(("_sync_real_index", _sync_check_then_write),))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(attempts[0], ("chmod", 0))
        self.assertFalse(self.no_lost_update(self.repo, attempts))

    def index_files(self):
        gitdir = os.path.join(self.repo, ".git")
        out = {}
        for name in os.listdir(gitdir):
            if name == "index" or name.startswith("sharedindex."):
                with open(os.path.join(gitdir, name), "rb") as fh:
                    out[name] = fh.read()
        return out

    def test_q2_split_index_left_alone(self):
        git(self.repo, "config", "core.splitIndex", "true")
        git(self.repo, "update-index", "--split-index")
        files = {}
        res, _ = self.fix_flow(self.fix30,
                               owner_after_seal=lambda: files.update(
                                   self.index_files()))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("index-left-as-is: f.txt", res.stdout.splitlines())
        self.assertTrue(any(n.startswith("sharedindex.") for n in files))
        now = self.index_files()
        for name, data in files.items():
            self.assertEqual(now.get(name), data, name)


if __name__ == "__main__":
    unittest.main()
