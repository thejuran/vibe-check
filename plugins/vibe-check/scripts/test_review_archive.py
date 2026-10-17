"""Tests for review_archive.py: archive names are unique, keep the phase, and
an existing archive is never overwritten (two same-day close-outs keep both
reports and both state archives).
"""

import ast
import errno
import os
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_archive  # noqa: E402

REVIEW_ARCHIVE_PY = os.path.join(HERE, "review_archive.py")
DATE = "2026-10-15"


def _write(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class TmpCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()


class TestArchiveName(TmpCase):
    BASE = "REVIEW-54-freeze-" + DATE

    def test_absent_returns_base(self):
        self.assertEqual(review_archive.archive_name(self.dir, self.BASE, ".md"),
                         self.BASE + ".md")

    def test_first_taken_returns_dash_two(self):
        _write(os.path.join(self.dir, self.BASE + ".md"), "a")
        self.assertEqual(review_archive.archive_name(self.dir, self.BASE, ".md"),
                         self.BASE + "-2.md")

    def test_two_taken_returns_dash_three(self):
        _write(os.path.join(self.dir, self.BASE + ".md"), "a")
        _write(os.path.join(self.dir, self.BASE + "-2.md"), "b")
        self.assertEqual(review_archive.archive_name(self.dir, self.BASE, ".md"),
                         self.BASE + "-3.md")

    def test_only_dash_two_present_returns_base(self):
        _write(os.path.join(self.dir, self.BASE + "-2.md"), "b")
        self.assertEqual(review_archive.archive_name(self.dir, self.BASE, ".md"),
                         self.BASE + ".md")

    def test_dangling_symlink_counts_as_taken(self):
        os.symlink(os.path.join(self.dir, "nowhere"),
                   os.path.join(self.dir, self.BASE + ".md"))
        self.assertEqual(review_archive.archive_name(self.dir, self.BASE, ".md"),
                         self.BASE + "-2.md")


class TestSafePhase(unittest.TestCase):
    def test_allowlisted_kept(self):
        for p in ("54", "54-freeze", "v2.12_a", "53.1"):
            with self.subTest(p=p):
                self.assertEqual(review_archive.safe_phase(p), p)

    def test_disallowed_becomes_unknown(self):
        for p in ("", "a/b", "../x", "a b", "54;rm", "x\n", None, "é"):
            with self.subTest(p=p):
                self.assertEqual(review_archive.safe_phase(p), "unknown")


class TestArchive(TmpCase):
    def test_report_two_same_day_both_preserved(self):
        base = "REVIEW-54-" + DATE
        first = os.path.join(self.dir, "REVIEW.md")
        _write(first, "first report")
        p1 = review_archive.archive(first, self.dir, base, ".md")
        _write(first, "second report")
        p2 = review_archive.archive(first, self.dir, base, ".md")
        self.assertEqual(os.path.basename(p1), base + ".md")
        self.assertEqual(os.path.basename(p2), base + "-2.md")
        self.assertEqual(_read(p1), "first report")
        self.assertEqual(_read(p2), "second report")
        self.assertFalse(os.path.exists(first))

    def test_state_archive_two_same_day_both_preserved(self):
        state = os.path.join(self.dir, "feat.json")
        base = "feat.json.archived-" + DATE
        _write(state, '{"pass": 1}')
        p1 = review_archive.archive(state, self.dir, base, "")
        _write(state, '{"pass": 2}')
        p2 = review_archive.archive(state, self.dir, base, "")
        self.assertEqual(os.path.basename(p1), base)
        self.assertEqual(os.path.basename(p2), base + "-2")
        self.assertEqual(_read(p1), '{"pass": 1}')
        self.assertEqual(_read(p2), '{"pass": 2}')

    def test_unstamped_two_same_day_both_preserved(self):
        base = "REVIEW-unstamped-" + DATE
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "old one")
        p1 = review_archive.archive(src, self.dir, base, ".md")
        _write(src, "old two")
        p2 = review_archive.archive(src, self.dir, base, ".md")
        self.assertEqual({_read(p1), _read(p2)}, {"old one", "old two"})
        self.assertNotEqual(p1, p2)

    def test_never_overwrites_when_name_collides(self):
        """Even if name selection returns a taken name, the move refuses."""
        base = "REVIEW-54-" + DATE
        taken = os.path.join(self.dir, base + ".md")
        _write(taken, "keep me")
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "new")
        with mock.patch.object(review_archive, "archive_name",
                               lambda d, b, s: b + s):
            with self.assertRaises(FileExistsError):
                review_archive.archive(src, self.dir, base, ".md")
        self.assertEqual(_read(taken), "keep me")
        self.assertEqual(_read(src), "new")

    def test_missing_source_raises(self):
        with self.assertRaises(FileNotFoundError):
            review_archive.archive(os.path.join(self.dir, "nope"), self.dir,
                                   "x", ".md")


class TestMutants(TmpCase):
    def _two_same_day_preserved(self, mod):
        base = "REVIEW-54-" + DATE
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "first")
        try:
            p1 = mod.archive(src, self.dir, base, ".md")
            _write(src, "second")
            p2 = mod.archive(src, self.dir, base, ".md")
        except OSError:
            return False
        return p1 != p2 and _read(p1) == "first" and _read(p2) == "second"

    def test_mutant_base_name_breaks_two_same_day(self):
        self.assertTrue(self._two_same_day_preserved(review_archive))
        for f in os.listdir(self.dir):
            os.unlink(os.path.join(self.dir, f))
        with mock.patch.object(review_archive, "archive_name",
                               lambda d, b, s: b + s):
            self.assertFalse(self._two_same_day_preserved(review_archive))

    def _replace_copy(self):
        with open(REVIEW_ARCHIVE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        mutated = src.replace("os.link(src, target)", "os.replace(src, target)")
        mutated = mutated.replace(
            "    try:\n        os.unlink(src)\n    except OSError as exc:\n"
            "        _release(target, src, exc)\n", "")
        self.assertNotEqual(mutated, src)
        mod = types.ModuleType("review_archive_replace_mutant")
        exec(compile(mutated, "review_archive_mutant", "exec"), mod.__dict__)
        return mod

    def _never_overwrites(self, mod):
        base = "REVIEW-54-" + DATE
        taken = os.path.join(self.dir, base + ".md")
        _write(taken, "keep me")
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "new")
        with mock.patch.object(mod, "archive_name", lambda d, b, s: b + s):
            try:
                mod.archive(src, self.dir, base, ".md")
            except FileExistsError:
                pass
        return _read(taken) == "keep me"

    def test_mutant_os_replace_overwrites(self):
        self.assertTrue(self._never_overwrites(review_archive))
        for f in os.listdir(self.dir):
            os.unlink(os.path.join(self.dir, f))
        self.assertFalse(self._never_overwrites(self._replace_copy()))


def _no_link(*_a, **_k):
    raise OSError(errno.EPERM, "Operation not permitted")


class TestNoHardLinkFallback(TmpCase):
    """Filesystems without hard links (exFAT/FAT, SMB, many FUSE mounts):
    os.link raises a non-FileExistsError OSError. The move falls back to an
    exclusive-create copy, never overwrites, and removes the source only
    after the copy is verified."""

    BASE = "REVIEW-54-" + DATE

    def test_fallback_archives_without_links(self):
        for err in (errno.EPERM, errno.ENOTSUP, errno.EXDEV, errno.EOPNOTSUPP,
                    errno.EMLINK, errno.ENOSYS):
            with self.subTest(errno=errno.errorcode[err]):
                src = os.path.join(self.dir, "REVIEW.md")
                _write(src, "report %d" % err)
                with mock.patch.object(review_archive.os, "link",
                                       side_effect=OSError(err, "no links")):
                    path = review_archive.archive(src, self.dir,
                                                  self.BASE + "-%d" % err, ".md")
                self.assertFalse(os.path.exists(src))
                self.assertEqual(_read(path), "report %d" % err)

    def test_fallback_two_same_day_both_preserved(self):
        src = os.path.join(self.dir, "REVIEW.md")
        with mock.patch.object(review_archive.os, "link", _no_link):
            _write(src, "first")
            p1 = review_archive.archive(src, self.dir, self.BASE, ".md")
            _write(src, "second")
            p2 = review_archive.archive(src, self.dir, self.BASE, ".md")
        self.assertEqual(os.path.basename(p1), self.BASE + ".md")
        self.assertEqual(os.path.basename(p2), self.BASE + "-2.md")
        self.assertEqual((_read(p1), _read(p2)), ("first", "second"))

    def test_fallback_never_overwrites(self):
        taken = os.path.join(self.dir, self.BASE + ".md")
        _write(taken, "keep me")
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "new")
        with mock.patch.object(review_archive.os, "link", _no_link), \
                mock.patch.object(review_archive, "archive_name",
                                  lambda d, b, s: b + s):
            with self.assertRaises(FileExistsError):
                review_archive.archive(src, self.dir, self.BASE, ".md")
        self.assertEqual(_read(taken), "keep me")
        self.assertEqual(_read(src), "new")

    def test_fallback_race_picks_next_name(self):
        """The chosen name is created by someone else between selection and
        the exclusive create: the next free name is used."""
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "mine")
        real = review_archive.archive_name
        calls = []

        def racing(d, b, s):
            name = real(d, b, s)
            if not calls:
                _write(os.path.join(d, name), "theirs")  # the race
            calls.append(name)
            return name

        with mock.patch.object(review_archive.os, "link", _no_link), \
                mock.patch.object(review_archive, "archive_name", racing):
            path = review_archive.archive(src, self.dir, self.BASE, ".md")
        self.assertEqual(os.path.basename(path), self.BASE + "-2.md")
        self.assertEqual(_read(os.path.join(self.dir, self.BASE + ".md")),
                         "theirs")
        self.assertEqual(_read(path), "mine")
        self.assertFalse(os.path.exists(src))

    def test_fallback_preserves_mode_and_bytes(self):
        src = os.path.join(self.dir, "feat.json")
        data = bytes(range(256)) * 41
        with open(src, "wb") as fh:
            fh.write(data)
        os.chmod(src, 0o640)
        with mock.patch.object(review_archive.os, "link", _no_link):
            path = review_archive.archive(src, self.dir, "feat.json.archived-"
                                          + DATE, "")
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), data)
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)

    def test_copy_mismatch_removes_copy_and_keeps_source(self):
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "the report")
        real_write = os.write

        def short_write(fd, data):
            return real_write(fd, bytes(data)[:3])  # silently truncated

        with mock.patch.object(review_archive.os, "link", _no_link), \
                mock.patch.object(review_archive, "_write_all", short_write):
            with self.assertRaises(OSError):
                review_archive.archive(src, self.dir, self.BASE, ".md")
        self.assertEqual(_read(src), "the report")
        self.assertEqual(sorted(os.listdir(self.dir)), ["REVIEW.md"])

    def test_total_failure_keeps_source(self):
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "the report")
        with mock.patch.object(review_archive.os, "link", _no_link), \
                mock.patch.object(review_archive.os, "open",
                                  side_effect=OSError(errno.EACCES, "denied")):
            with self.assertRaises(OSError):
                review_archive.archive(src, self.dir, self.BASE, ".md")
        self.assertEqual(_read(src), "the report")
        self.assertEqual(os.listdir(self.dir), ["REVIEW.md"])


class TestSourceRemovalFailure(TmpCase):
    """bugs-007: when the source cannot be removed after the archive name was
    claimed, the archive name is released again so exactly one live copy
    remains; if that also fails, the error names both paths."""

    BASE = "feat.json.archived-" + DATE

    def _unlink_fails_for(self, victim):
        real = os.unlink

        def unlink(path, *a, **k):
            if os.path.abspath(path) == os.path.abspath(victim):
                raise OSError(errno.EBUSY, "busy")
            return real(path, *a, **k)
        return unlink

    def test_link_path_undoes_archive(self):
        src = os.path.join(self.dir, "feat.json")
        _write(src, "{}")
        with mock.patch.object(review_archive.os, "unlink",
                               self._unlink_fails_for(src)):
            with self.assertRaises(OSError) as cm:
                review_archive.archive(src, self.dir, self.BASE, "")
        self.assertEqual(os.listdir(self.dir), ["feat.json"])
        self.assertIn(src, str(cm.exception))

    def test_copy_path_undoes_archive(self):
        src = os.path.join(self.dir, "feat.json")
        _write(src, "{}")
        with mock.patch.object(review_archive.os, "link", _no_link), \
                mock.patch.object(review_archive.os, "unlink",
                                  self._unlink_fails_for(src)):
            with self.assertRaises(OSError):
                review_archive.archive(src, self.dir, self.BASE, "")
        self.assertEqual(os.listdir(self.dir), ["feat.json"])
        self.assertEqual(_read(src), "{}")

    def test_both_removals_fail_names_both_paths(self):
        src = os.path.join(self.dir, "feat.json")
        _write(src, "{}")
        target = os.path.join(self.dir, self.BASE)

        def unlink(path, *a, **k):
            raise OSError(errno.EBUSY, "busy")

        with mock.patch.object(review_archive.os, "unlink", unlink):
            with self.assertRaises(OSError) as cm:
                review_archive.archive(src, self.dir, self.BASE, "")
        msg = str(cm.exception)
        self.assertIn(src, msg)
        self.assertIn(target, msg)
        self.assertIn("both", msg)


class TestFallbackMutants(TmpCase):
    """Each new guard trips when removed."""

    def _mutant(self, old, new):
        with open(REVIEW_ARCHIVE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        mutated = src.replace(old, new)
        self.assertNotEqual(mutated, src)
        mod = types.ModuleType("review_archive_mutant")
        exec(compile(mutated, "review_archive_mutant", "exec"), mod.__dict__)
        return mod

    def _fallback_works(self, mod):
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "x")
        try:
            with mock.patch.object(mod.os, "link", _no_link):
                path = mod.archive(src, self.dir, "R", ".md")
        except OSError:
            return False
        return _read(path) == "x" and not os.path.exists(src)

    def _fallback_no_clobber(self, mod):
        taken = os.path.join(self.dir, "R.md")
        _write(taken, "keep me")
        src = os.path.join(self.dir, "REVIEW.md")
        _write(src, "new")
        with mock.patch.object(mod.os, "link", _no_link), \
                mock.patch.object(mod, "archive_name", lambda d, b, s: b + s):
            try:
                mod.archive(src, self.dir, "R", ".md")
            except OSError:
                pass
        return _read(taken) == "keep me"

    def _undo_on_unlink_failure(self, mod):
        src = os.path.join(self.dir, "feat.json")
        _write(src, "{}")
        real = os.unlink

        def unlink(path, *a, **k):
            if os.path.abspath(path) == os.path.abspath(src):
                raise OSError(errno.EBUSY, "busy")
            return real(path, *a, **k)
        with mock.patch.object(mod.os, "unlink", unlink):
            try:
                mod.archive(src, self.dir, "feat.json.archived", "")
            except OSError:
                pass
        return os.listdir(self.dir) == ["feat.json"]

    def _clear(self):
        for f in os.listdir(self.dir):
            os.unlink(os.path.join(self.dir, f))

    def test_mutant_no_fallback(self):
        self.assertTrue(self._fallback_works(review_archive))
        self._clear()
        mod = self._mutant("        _copy_no_clobber(src, target)\n",
                           "        raise\n")
        self.assertFalse(self._fallback_works(mod))

    def test_mutant_fallback_without_excl(self):
        self.assertTrue(self._fallback_no_clobber(review_archive))
        self._clear()
        mod = self._mutant("os.O_CREAT | os.O_EXCL | os.O_WRONLY",
                           "os.O_CREAT | os.O_TRUNC | os.O_WRONLY")
        self.assertFalse(self._fallback_no_clobber(mod))

    def test_mutant_no_undo_on_unlink_failure(self):
        self.assertTrue(self._undo_on_unlink_failure(review_archive))
        self._clear()
        mod = self._mutant("        _release(target, src, exc)\n",
                           "        raise\n")
        self.assertFalse(self._undo_on_unlink_failure(mod))


class TestCLI(TmpCase):
    def _run(self, argv):
        return subprocess.run(
            [sys.executable, REVIEW_ARCHIVE_PY] + argv,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

    def test_review_md_two_same_day(self):
        tm = os.path.join(self.dir, ".turingmind")
        os.mkdir(tm)
        src = os.path.join(tm, "REVIEW.md")
        outs = []
        for body in ("one", "two"):
            _write(src, body)
            proc = self._run(["review-md", "--phase", "54-freeze", "--dir", tm,
                              "--date", DATE])
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            outs.append(proc.stdout.decode().strip())
        self.assertEqual(os.path.basename(outs[0]),
                         "REVIEW-54-freeze-%s.md" % DATE)
        self.assertEqual(os.path.basename(outs[1]),
                         "REVIEW-54-freeze-%s-2.md" % DATE)
        self.assertEqual([_read(p) for p in outs], ["one", "two"])

    def test_review_md_bad_phase_becomes_unknown(self):
        _write(os.path.join(self.dir, "REVIEW.md"), "x")
        proc = self._run(["review-md", "--phase", "../../etc", "--dir",
                          self.dir, "--date", DATE])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = proc.stdout.decode().strip()
        self.assertEqual(os.path.dirname(out), self.dir)
        self.assertEqual(os.path.basename(out),
                         "REVIEW-unknown-%s.md" % DATE)

    def test_unstamped_cli(self):
        _write(os.path.join(self.dir, "REVIEW.md"), "x")
        proc = self._run(["unstamped", "--dir", self.dir, "--date", DATE])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(os.path.basename(proc.stdout.decode().strip()),
                         "REVIEW-unstamped-%s.md" % DATE)

    def test_state_archive_two_same_day_cli(self):
        state = os.path.join(self.dir, "feat.json")
        outs = []
        for body in ("1", "2"):
            _write(state, body)
            proc = self._run(["state", "--state-file", state, "--date", DATE])
            self.assertEqual(proc.returncode, 0, proc.stderr.decode())
            outs.append(proc.stdout.decode().strip())
        self.assertEqual([os.path.basename(p) for p in outs],
                         ["feat.json.archived-" + DATE,
                          "feat.json.archived-%s-2" % DATE])
        self.assertEqual([_read(p) for p in outs], ["1", "2"])

    def test_default_date_is_local_today(self):
        _write(os.path.join(self.dir, "REVIEW.md"), "x")
        today = subprocess.run(["date", "+%Y-%m-%d"], stdout=subprocess.PIPE,
                               timeout=30).stdout.decode().strip()
        proc = self._run(["unstamped", "--dir", self.dir])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(os.path.basename(proc.stdout.decode().strip()),
                         "REVIEW-unstamped-%s.md" % today)

    def test_missing_source_exits_one(self):
        for argv in (["review-md", "--phase", "54", "--dir", self.dir],
                     ["unstamped", "--dir", self.dir],
                     ["state", "--state-file", os.path.join(self.dir, "x.json")]):
            with self.subTest(argv=argv[0]):
                proc = self._run(argv)
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(len(proc.stderr.decode().strip().splitlines()), 1)

    def test_unarchivable_exits_one_and_keeps_source(self):
        if os.geteuid() == 0:
            self.skipTest("root ignores directory permissions")
        tm = os.path.join(self.dir, "ro")
        os.mkdir(tm)
        src = os.path.join(tm, "REVIEW.md")
        _write(src, "prior report")
        os.chmod(tm, 0o555)
        try:
            proc = self._run(["review-md", "--phase", "54", "--dir", tm,
                              "--date", DATE])
        finally:
            os.chmod(tm, 0o755)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, b"")
        self.assertIn("left in place", proc.stderr.decode())
        self.assertEqual(os.listdir(tm), ["REVIEW.md"])
        self.assertEqual(_read(src), "prior report")

    def test_usage_errors_exit_two(self):
        for argv in (["bogus"], [], ["review-md"], ["state"],
                     ["unstamped", "--date", "15-10-2026"],
                     ["unstamped", "--date", "2026-13-01"],
                     ["review-md", "--phase", "54", "--extra"]):
            with self.subTest(argv=argv):
                proc = self._run(argv)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")


class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "datetime", "os", "sys"}
    FORBIDDEN = {"subprocess", "shutil", "json", "pathlib", "glob"}

    def _imported(self):
        with open(REVIEW_ARCHIVE_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        return imported

    def test_import_set_exact(self):
        self.assertEqual(self._imported(), self.ALLOWED)

    def test_no_forbidden_import(self):
        self.assertFalse(self._imported() & self.FORBIDDEN)

    def test_no_replace_or_rename_call(self):
        with open(REVIEW_ARCHIVE_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        self.assertIn("link", attrs)
        self.assertFalse(attrs & {"replace", "rename", "renames"})


if __name__ == "__main__":
    unittest.main()
