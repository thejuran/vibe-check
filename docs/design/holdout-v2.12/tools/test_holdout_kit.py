"""Tests for holdout_kit — the owner-run launch kit for the v2.12 holdout.

Locked here:
  * Shared helpers: strict JSON load, atomic JSON write (no .tmp left behind),
    argv subprocess with timeout (never shell), symlink-refusing walk, safe tar
    extraction (absolute, `..` and link members refused), case-id listing.
  * D-15: every holdout command refuses inside a Claude-spawned shell unless
    the session's own config dir lives inside the holdout folder; the folder
    is always explicit (no argparse default names the holdout path).
  * Lazy dispatch: a sibling module that is not installed yet reports a plain
    "not installed" line; NO_FOLDER_COMMANDS is the one opt-out from --folder
    (mutation-tested).
  * Module shape: exact import set, every subprocess.run has a timeout and no
    shell, no openssl argv carries -pass/-k. Each lock is also run against a
    synthetic violation so it is known to be able to trip.

Mutants follow the gitsnap convention: first show the real component sees the
difference, then patch it out and show the case is no longer caught.
"""

import ast
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
from holdout_fixture import git, write  # noqa: E402

KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")

# Module files under the shape locks. Later plans append their own module
# filenames here; each later module's exact import set is asserted in its own
# test file.
MODULES = ["holdout_kit.py"]


def _clean_env():
    """Patch os.environ for in-process kit calls (no CLAUDECODE)."""
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CONFIG_DIR", None)
    return mock.patch.dict(os.environ, env, clear=True)


class KitCase(unittest.TestCase):
    """Base: a realpath temp dir, a clean in-process env and a CLI runner."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self._env = _clean_env()
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def cli(self, *args, env=None, cwd=None):
        return subprocess.run(
            [sys.executable, KIT_PY, *args], cwd=cwd or self.tmp,
            env=env if env is not None else holdout_fixture.kit_env(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=120)

    def run_inproc(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdout", out), \
                mock.patch.object(sys, "stderr", err):
            rc = holdout_kit.run(argv)
        return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------- refusal


class TestRefusal(KitCase):

    def test_refuses_when_claudecode_and_no_config_dir(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            with self.assertRaises(holdout_kit.KitError) as cm:
                holdout_kit.refuse_if_claude_spawned(self.tmp)
        self.assertEqual(str(cm.exception), holdout_kit.REFUSE_MSG)

    def test_allows_when_claudecode_unset(self):
        holdout_kit.refuse_if_claude_spawned(self.tmp)

    def test_allows_when_config_dir_inside_folder(self):
        cfg = os.path.join(self.tmp, "cfg-finder")
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1",
                                          "CLAUDE_CONFIG_DIR": cfg}):
            holdout_kit.refuse_if_claude_spawned(self.tmp)

    def test_refuses_when_config_dir_is_a_sibling(self):
        folder = os.path.join(self.tmp, "h")
        sibling = os.path.join(self.tmp, "h-other", "cfg")
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1",
                                          "CLAUDE_CONFIG_DIR": sibling}):
            with self.assertRaises(holdout_kit.KitError):
                holdout_kit.refuse_if_claude_spawned(folder)

    def test_refuses_prefix_named_sibling(self):
        # "<h>x" shares the string prefix of "<h>" but is not inside it.
        folder = os.path.join(self.tmp, "h")
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1",
                                          "CLAUDE_CONFIG_DIR": folder + "x"}):
            with self.assertRaises(holdout_kit.KitError):
                holdout_kit.refuse_if_claude_spawned(folder)

    def test_refuses_when_folder_is_none(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1",
                                          "CLAUDE_CONFIG_DIR": self.tmp}):
            with self.assertRaises(holdout_kit.KitError):
                holdout_kit.refuse_if_claude_spawned(None)

    def test_cli_setup_refuses_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("--folder", os.path.join(self.tmp, "h"), "setup",
                        "--repo", self.tmp, env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr, holdout_kit.REFUSE_MSG + "\n")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "h")))


# ---------------------------------------------------------------- helpers


class TestLoadJson(KitCase):

    def _p(self, data):
        path = os.path.join(self.tmp, "x.json")
        with open(path, "w") as fh:
            fh.write(data)
        return path

    def test_missing_file(self):
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.load_json(os.path.join(self.tmp, "nope.json"),
                                  what="the key file")
        self.assertIn("the key file", str(cm.exception))
        self.assertIn("missing or unreadable", str(cm.exception))

    def test_invalid_json(self):
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.load_json(self._p("{not json"), what="k")
        self.assertIn("missing or unreadable", str(cm.exception))

    def test_list_is_wrong_shape(self):
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.load_json(self._p("[1, 2]"), what="k")
        self.assertIn("wrong shape", str(cm.exception))

    def test_missing_required_key(self):
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.load_json(self._p('{"a": 1}'), required=("b",),
                                  what="k")
        self.assertIn("wrong shape (b)", str(cm.exception))

    def test_bool_does_not_satisfy_int(self):
        path = self._p('{"n": true}')
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.load_json(path, required={"n": int}, what="k")
        self.assertIn("wrong shape (n)", str(cm.exception))
        self.assertEqual(holdout_kit.load_json(
            self._p('{"n": 3}'), required={"n": int}), {"n": 3})


class TestWriteJsonAtomic(KitCase):

    def test_round_trip_sorted_with_newline(self):
        path = os.path.join(self.tmp, "sub", "o.json")
        holdout_kit.write_json_atomic(path, {"b": 1, "a": [1]})
        with open(path) as fh:
            text = fh.read()
        self.assertTrue(text.endswith("\n"))
        self.assertLess(text.index('"a"'), text.index('"b"'))
        self.assertEqual(json.loads(text), {"a": [1], "b": 1})

    def test_failure_leaves_no_tmp_and_destination_unchanged(self):
        path = os.path.join(self.tmp, "o.json")
        holdout_kit.write_json_atomic(path, {"v": 1})
        with mock.patch.object(holdout_kit.os, "replace",
                               side_effect=OSError("boom")):
            with self.assertRaises(holdout_kit.KitError):
                holdout_kit.write_json_atomic(path, {"v": 2})
        self.assertEqual(sorted(os.listdir(self.tmp)), ["o.json"])
        with open(path) as fh:
            self.assertEqual(json.load(fh), {"v": 1})


class TestRunArgv(KitCase):

    def test_runs_argv(self):
        proc = holdout_kit.run_argv(["git", "--version"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn(b"git version", proc.stdout)

    def test_missing_binary_raises(self):
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.run_argv(["/nonexistent/x"])
        self.assertIn("could not run", str(cm.exception))
        self.assertTrue(str(cm.exception).startswith("x "))

    def test_timeout_raises(self):
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.run_argv(["sleep", "1"], timeout=0.01)
        self.assertIn("could not run", str(cm.exception))
        self.assertIn("sleep", str(cm.exception))
        self.assertNotIn("/", str(cm.exception))

    def test_stdin_bytes(self):
        proc = holdout_kit.run_argv(["cat"], stdin_bytes=b"abc")
        self.assertEqual(proc.stdout, b"abc")


class TestHashes(unittest.TestCase):

    def test_sha256_and_hmac(self):
        import hashlib
        import hmac
        self.assertEqual(holdout_kit.sha256_bytes(b"x"),
                         hashlib.sha256(b"x").hexdigest())
        self.assertEqual(holdout_kit.hmac_hex(b"k", b"m"),
                         hmac.new(b"k", b"m", hashlib.sha256).hexdigest())
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fh.write(b"abc")
        try:
            self.assertEqual(holdout_kit.sha256_file(fh.name),
                             hashlib.sha256(b"abc").hexdigest())
        finally:
            os.remove(fh.name)


class TestWalkRegular(KitCase):

    def test_sorted_relpaths(self):
        write(self.tmp, "b/2.txt", "x")
        write(self.tmp, "a.txt", "x")
        write(self.tmp, "b/1.txt", "x")
        self.assertEqual(holdout_kit.walk_regular(self.tmp),
                         ["a.txt", "b/1.txt", "b/2.txt"])

    def test_file_symlink_refused(self):
        write(self.tmp, "a.txt", "x")
        link = os.path.join(self.tmp, "l")
        os.symlink(os.path.join(self.tmp, "a.txt"), link)
        self.assertTrue(os.path.islink(link))
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.walk_regular(self.tmp)

    def test_dir_symlink_refused(self):
        os.makedirs(os.path.join(self.tmp, "real"))
        write(self.tmp, "real/f", "x")
        link = os.path.join(self.tmp, "sub", "ld")
        os.makedirs(os.path.dirname(link))
        os.symlink(os.path.join(self.tmp, "real"), link)
        self.assertTrue(os.path.islink(link))
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.walk_regular(self.tmp)

    def test_fifo_refused(self):
        fifo = os.path.join(self.tmp, "p")
        os.mkfifo(fifo)
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.walk_regular(self.tmp)


class TestSafeExtractTar(KitCase):

    def _tar(self, members):
        path = os.path.join(self.tmp, "t.tar")
        with tarfile.open(path, "w") as tar:
            for info, data in members:
                tar.addfile(info, io.BytesIO(data) if data is not None
                            else None)
        return path

    def _file(self, name, data=b"hi"):
        info = tarfile.TarInfo(name)
        info.size = len(data)
        return info, data

    def test_plain_tar_extracts(self):
        path = self._tar([self._file("a.txt", b"A"),
                          self._file("d/b.txt", b"B")])
        dest = os.path.join(self.tmp, "out")
        os.makedirs(dest)
        holdout_kit.safe_extract_tar(path, dest)
        with open(os.path.join(dest, "a.txt"), "rb") as fh:
            self.assertEqual(fh.read(), b"A")
        with open(os.path.join(dest, "d", "b.txt"), "rb") as fh:
            self.assertEqual(fh.read(), b"B")

    def test_absolute_member_refused(self):
        path = self._tar([self._file("/abs/evil.txt")])
        with tarfile.open(path) as tar:
            self.assertTrue(any(n.startswith("/") for n in tar.getnames()))
        dest = os.path.join(self.tmp, "out")
        os.makedirs(dest)
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.safe_extract_tar(path, dest)
        self.assertEqual(os.listdir(dest), [])

    def test_dotdot_member_refused(self):
        path = self._tar([self._file("../x")])
        with tarfile.open(path) as tar:
            self.assertIn("../x", tar.getnames())
        dest = os.path.join(self.tmp, "out")
        os.makedirs(dest)
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.safe_extract_tar(path, dest)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "x")))

    def test_symlink_member_refused(self):
        info = tarfile.TarInfo("link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        path = self._tar([(info, None)])
        with tarfile.open(path) as tar:
            self.assertTrue(tar.getmember("link").issym())
        dest = os.path.join(self.tmp, "out")
        os.makedirs(dest)
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.safe_extract_tar(path, dest)
        self.assertFalse(os.path.lexists(os.path.join(dest, "link")))

    def test_hardlink_member_refused(self):
        info = tarfile.TarInfo("hl")
        info.type = tarfile.LNKTYPE
        info.linkname = "a.txt"
        path = self._tar([self._file("a.txt"), (info, None)])
        with tarfile.open(path) as tar:
            self.assertTrue(tar.getmember("hl").islnk())
        dest = os.path.join(self.tmp, "out")
        os.makedirs(dest)
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.safe_extract_tar(path, dest)


class TestCaseIds(KitCase):

    def test_sorted_matching(self):
        cases = os.path.join(self.tmp, "sealed", "cases")
        for name in ("H-0000000b", "H-0000000a"):
            os.makedirs(os.path.join(cases, name))
        self.assertEqual(holdout_kit.case_ids(self.tmp),
                         ["H-0000000a", "H-0000000b"])
        self.assertEqual(holdout_kit.sealed_dir(self.tmp),
                         os.path.join(self.tmp, "sealed"))

    def test_junk_name_refused(self):
        os.makedirs(os.path.join(self.tmp, "sealed", "cases", "junk"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.case_ids(self.tmp)

    def test_id_regexes(self):
        self.assertTrue(holdout_kit.ID_RE.match("H-0123abcd"))
        self.assertFalse(holdout_kit.ID_RE.match("H-0123ABCD"))
        self.assertTrue(holdout_kit.XID_RE.match("X-0123abcd"))
        self.assertEqual(holdout_kit.SLOTS,
                         ("C1", "C2", "C3", "Q1", "Q2", "Q3"))


class TestPrintHelpers(unittest.TestCase):

    def test_ok_and_problem(self):
        out = io.StringIO()
        with mock.patch.object(sys, "stdout", out):
            self.assertIsNone(holdout_kit.print_ok("a"))
            self.assertIsNone(holdout_kit.print_problem("b"))
        self.assertEqual(out.getvalue(), "OK: a\nPROBLEM: b\n")


# ---------------------------------------------------------------- dispatch


STUB_SRC = '''
import argparse
RECORD = {}

def add_parser(sub, name):
    p = sub.add_parser(name)
    if name in ("seal-order", "publish"):
        p.add_argument("--repo", required=True)

def cmd(args):
    RECORD["folder"] = args.folder
    RECORD["cmd"] = args.cmd
    return 7
'''


class TestDispatch(KitCase):

    def test_help_returns_zero(self):
        rc, out, _ = self.run_inproc(["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("setup", out)

    def test_cli_help_lists_setup(self):
        proc = self.cli("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("setup", proc.stdout)

    def test_unknown_command_is_usage_error(self):
        rc, _, _ = self.run_inproc(["--folder", self.tmp, "nonexistent-command"])
        self.assertEqual(rc, 2)

    def test_no_command_is_usage_error(self):
        rc, _, _ = self.run_inproc(["--folder", self.tmp])
        self.assertEqual(rc, 2)

    def test_missing_module_reports_not_installed(self):
        with mock.patch.dict(holdout_kit.COMMANDS,
                             {"validate": "no_such_holdout_module_xyz"}):
            rc, _, err = self.run_inproc(["--folder", self.tmp, "validate"])
        self.assertEqual(rc, 1)
        self.assertEqual(err, "holdout: command 'validate' is not installed "
                              "in this kit copy\n")

    def test_commands_table(self):
        c = holdout_kit.COMMANDS
        self.assertEqual(c["setup"], "holdout_kit")
        self.assertEqual(c["validate"], "holdout_validate")
        for name in ("seal-build", "rehash", "extract", "seal-order",
                     "publish", "retire", "resume-check"):
            self.assertEqual(c[name], "holdout_manifest")
        for name in ("crosscheck-prepare", "crosscheck-reveal",
                     "crosscheck-reset", "seal"):
            self.assertEqual(c[name], "holdout_seal")
        for name in ("encrypt", "leakscan", "scrub", "decrypt"):
            self.assertEqual(c[name], "holdout_archive")
        self.assertEqual(c["dryrun"], "holdout_dryrun")
        self.assertTrue(holdout_kit.NO_REFUSAL_COMMANDS
                        <= holdout_kit.NO_FOLDER_COMMANDS)

    def test_decrypt_requires_folder(self):
        # decrypt is a recovery command over the holdout archive: it is a
        # folder command, never a NO_FOLDER one, before and after its module
        # lands.
        self.assertNotIn("decrypt", holdout_kit.NO_FOLDER_COMMANDS)
        self.assertNotIn("decrypt", holdout_kit.NO_REFUSAL_COMMANDS)
        rc, _, err = self.run_inproc(["decrypt"])
        self.assertEqual(rc, 2)
        self.assertIn("--folder", err)

    def test_decrypt_dispatches_through_lazy_loader(self):
        with mock.patch.dict(holdout_kit.COMMANDS,
                             {"decrypt": "no_such_holdout_module_xyz"}):
            rc, _, err = self.run_inproc(["--folder", self.tmp, "decrypt"])
        self.assertEqual(rc, 1)
        self.assertIn("command 'decrypt' is not installed", err)

    def test_kit_error_becomes_exit_1(self):
        rc, _, err = self.run_inproc(["--folder", os.path.join(self.tmp, "h"),
                                      "setup", "--repo",
                                      os.path.join(self.tmp, "no-repo")])
        self.assertEqual(rc, 1)
        self.assertTrue(err.startswith("holdout: "))
        self.assertEqual(err.count("holdout: "), 1)


class TestNoFolderDispatch(KitCase):

    def setUp(self):
        super().setUp()
        self.stubdir = os.path.join(self.tmp, "stubs")
        os.makedirs(self.stubdir)
        with open(os.path.join(self.stubdir, "stub_resume.py"), "w") as fh:
            fh.write(STUB_SRC)
        sys.path.insert(0, self.stubdir)
        sys.modules.pop("stub_resume", None)

    def tearDown(self):
        sys.path.remove(self.stubdir)
        sys.modules.pop("stub_resume", None)
        super().tearDown()

    def _stubbed(self, name):
        return mock.patch.dict(holdout_kit.COMMANDS, {name: "stub_resume"})

    def test_set_is_exact(self):
        self.assertEqual(holdout_kit.NO_FOLDER_COMMANDS,
                         frozenset({"seal-order", "publish", "resume-check"}))

    def test_folder_command_without_folder_is_usage_error(self):
        rc, _, err = self.run_inproc(["setup"])
        self.assertEqual(rc, 2)
        self.assertIn("--folder", err)

    def test_resume_check_dispatches_without_folder(self):
        with self._stubbed("resume-check"):
            rc, _, _ = self.run_inproc(["resume-check"])
        self.assertEqual(rc, 7)
        stub = sys.modules["stub_resume"]
        self.assertIsNone(stub.RECORD["folder"])
        self.assertEqual(stub.RECORD["cmd"], "resume-check")

    def test_seal_order_dispatches_without_folder(self):
        with self._stubbed("seal-order"):
            rc, _, _ = self.run_inproc(["seal-order", "--repo", self.tmp])
        self.assertEqual(rc, 7)
        self.assertIsNone(sys.modules["stub_resume"].RECORD["folder"])

    def test_publish_dispatches_without_folder(self):
        with self._stubbed("publish"):
            rc, _, _ = self.run_inproc(["publish", "--repo", self.tmp])
        self.assertEqual(rc, 7)
        self.assertIsNone(sys.modules["stub_resume"].RECORD["folder"])

    def test_mutant_empty_set_blocks_resume_check(self):
        with self._stubbed("resume-check"):
            rc, _, _ = self.run_inproc(["resume-check"])
            self.assertEqual(rc, 7)
            with mock.patch.object(holdout_kit, "NO_FOLDER_COMMANDS",
                                   frozenset()):
                rc, _, err = self.run_inproc(["resume-check"])
        self.assertEqual(rc, 2)
        self.assertIn("--folder", err)


# ---------------------------------------------------------------- module shape


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


def _subprocess_run_violations(tree):
    bad = []
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
             and getattr(n.func.value, "id", None) == "subprocess"]
    for call in calls:
        kws = {k.arg for k in call.keywords}
        if "timeout" not in kws or "shell" in kws:
            bad.append(call.lineno)
    return calls, bad


def _holdout_default_violations(tree):
    bad = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("add_argument", "set_defaults")):
            for kw in node.keywords:
                for sub in ast.walk(kw.value):
                    if (isinstance(sub, ast.Constant)
                            and isinstance(sub.value, str)
                            and "vibe-check-holdout" in sub.value):
                        bad.append(node.lineno)
    return bad


def _openssl_secret_violations(tree):
    bad = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        strs = [e.value for e in node.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if not any("openssl" in s for s in strs):
            continue
        for s in strs:
            if "-pass" in s or "-k " in s or s == "-k":
                bad.append(node.lineno)
    return bad


class TestModuleShape(unittest.TestCase):

    def _tree(self, name):
        with open(os.path.join(TOOLS_DIR, name)) as fh:
            return ast.parse(fh.read())

    def test_kit_import_set_is_exact(self):
        self.assertEqual(_imports(self._tree("holdout_kit.py")),
                         {"argparse", "hashlib", "hmac", "importlib", "json",
                          "os", "re", "secrets", "shutil", "stat",
                          "subprocess", "sys", "tarfile", "tempfile"})

    def test_every_subprocess_run_has_timeout_and_no_shell(self):
        total = 0
        for name in MODULES:
            calls, bad = _subprocess_run_violations(self._tree(name))
            total += len(calls)
            self.assertEqual(bad, [], name)
        self.assertTrue(total)

    def test_subprocess_lock_can_trip(self):
        tree = ast.parse("import subprocess\nsubprocess.run(['x'], shell=True)"
                         "\nsubprocess.run(['y'])\n")
        _, bad = _subprocess_run_violations(tree)
        self.assertEqual(len(bad), 2)

    def test_no_argparse_default_names_holdout(self):
        for name in MODULES:
            self.assertEqual(_holdout_default_violations(self._tree(name)),
                             [], name)

    def test_default_lock_can_trip(self):
        tree = ast.parse("p.add_argument('--folder', "
                         "default='~/.vibe-check-holdout/v2.12')\n")
        self.assertEqual(len(_holdout_default_violations(tree)), 1)

    def test_no_openssl_secret_flags(self):
        for name in MODULES:
            self.assertEqual(_openssl_secret_violations(self._tree(name)),
                             [], name)

    def test_openssl_lock_can_trip(self):
        tree = ast.parse("a = ['/usr/bin/openssl', 'enc', '-pass', 'pass:x']\n"
                         "b = ['openssl', '-k', 'x']\n")
        self.assertEqual(len(_openssl_secret_violations(tree)), 2)

    def test_no_shell_true_in_source(self):
        with open(KIT_PY) as fh:
            lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
        self.assertFalse(any("shell=True" in ln for ln in lines))

    def test_run_and_commands_exported(self):
        self.assertTrue(callable(holdout_kit.run))
        self.assertIsInstance(holdout_kit.COMMANDS, dict)
        for name in ("KitError", "refuse_if_claude_spawned", "load_json",
                     "write_json_atomic", "run_argv", "sha256_file",
                     "sha256_bytes", "hmac_hex", "walk_regular",
                     "safe_extract_tar", "case_ids", "CASE_FILES",
                     "KEY_FILES", "SEALED_PRIVATE", "SANDBOX_SENTINEL_TEXT"):
            self.assertTrue(hasattr(holdout_kit, name), name)

    def test_no_import_from_plugin(self):
        for name in os.listdir(TOOLS_DIR):
            if name.endswith(".py"):
                imported = _imports(self._tree(name))
                self.assertNotIn("gitfixture", imported, name)
                self.assertFalse(any(m and m.startswith("plugins")
                                     for m in imported), name)


if __name__ == "__main__":
    unittest.main()
