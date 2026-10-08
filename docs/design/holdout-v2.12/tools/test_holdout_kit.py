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
MODULES = ["holdout_kit.py", "holdout_validate.py", "holdout_dryrun.py"]


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


# ================================================================ setup

import errno  # noqa: E402
import glob  # noqa: E402
import hashlib  # noqa: E402
import re  # noqa: E402
import runpy  # noqa: E402
import shutil  # noqa: E402
import stat  # noqa: E402

import holdout_guard  # noqa: E402

KIT_DIR = os.path.normpath(os.path.join(TOOLS_DIR, "..", "kit"))
REPO_ROOT = os.path.normpath(os.path.join(TOOLS_DIR, "..", "..", "..", ".."))
B3_DIFFS = os.path.join(REPO_ROOT, "docs", "design", "b3-ground-truth",
                        "diffs")
TOKENS = ("<H>", "<HOME>", "<REPOS>", "<GUARD>", "<SEALED>")
REFUSE_LINE = ('[ -z "${CLAUDECODE:-}" ] || { echo "Open a new Terminal '
               'window (not one started by Claude) and run this again."; '
               'exit 1; }')


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def _hook_args(settings):
    return settings["hooks"]["PreToolUse"][0]["hooks"][0]["args"]


def _protects(args):
    return [args[i + 1] for i, a in enumerate(args[:-1]) if a == "--protect"]


def _deny_read(settings):
    return settings["sandbox"]["filesystem"]["denyRead"]


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _strings(v)


def _quiet():
    return mock.patch.object(sys, "stdout", io.StringIO())


class SetupCase(KitCase):
    """Base: a holdout built by the real setup CLI at self.F."""

    def setUp(self):
        super().setUp()
        self.F = holdout_fixture.make_fake_holdout(self.tmp)
        self.repo = os.path.join(self.tmp, "src-repo")

    def inproc_setup(self, name):
        folder = os.path.join(self.tmp, name)
        with _quiet():
            holdout_kit.setup(folder, [self.repo],
                              skip_system_exclusions=True)
        return os.path.realpath(folder)

    def strip_gen1(self, F):
        n = holdout_kit.xcheck_names(1)
        for key in ("workspace", "config_dir", "tmp_dir"):
            shutil.rmtree(os.path.join(F, n[key]))
        os.remove(os.path.join(F, n["launcher"]))

    def finder_settings(self, F=None):
        return _load(os.path.join(F or self.F, "work", ".claude",
                                  "settings.json"))

    def xcheck_settings(self, ws="xcheck", F=None):
        return _load(os.path.join(F or self.F, ws, ".claude",
                                  "settings.json"))


class TestSetup(SetupCase):

    def test_layout(self):
        F = self.F
        for rel in holdout_kit.SUBDIRS:
            self.assertTrue(os.path.isdir(os.path.join(F, rel)), rel)
        self.assertEqual(_mode(F), 0o700)
        for rel in ("tmp/finder", "tmp/owner"):
            self.assertEqual(_mode(os.path.join(F, rel)), 0o700, rel)
            self.assertEqual(_read(os.path.join(F, rel, "SANDBOX-SENTINEL")),
                             holdout_kit.SANDBOX_SENTINEL_TEXT)
        self.assertEqual(_read(os.path.join(F, ".metadata_never_index")), "")
        self.assertEqual(_read(os.path.join(F, "sealed", "SANDBOX-SENTINEL")),
                         holdout_kit.SANDBOX_SENTINEL_TEXT)
        self.assertEqual(sorted(os.listdir(os.path.join(F, "sealed"))),
                         ["SANDBOX-SENTINEL", "cases", "keys"])
        self.assertEqual(sorted(os.listdir(os.path.join(F, "tmp"))),
                         ["crosscheck", "finder", "owner"])
        self.assertEqual(os.listdir(os.path.join(F, "tmp", "crosscheck")),
                         ["xcheck"])
        self.assertEqual(sorted(os.listdir(os.path.join(F, "bin"))),
                         ["crosscheck", "finder", "holdout"])
        for name in ("crosscheck", "finder", "holdout"):
            self.assertEqual(_mode(os.path.join(F, "bin", name)), 0o700)

    def test_kit_and_tools_copied(self):
        kit = os.path.join(self.F, "kit")
        for name in os.listdir(KIT_DIR):
            if name.endswith((".md", ".json")):
                with open(os.path.join(KIT_DIR, name), "rb") as a, \
                        open(os.path.join(kit, name), "rb") as b:
                    self.assertEqual(a.read(), b.read(), name)
        tools = sorted(os.listdir(os.path.join(kit, "tools")))
        expected = sorted(n for n in os.listdir(TOOLS_DIR)
                          if n.endswith(".py") and not n.startswith("test_"))
        self.assertEqual(tools, expected)
        self.assertIn("holdout_kit.py", tools)
        self.assertTrue(os.path.isfile(os.path.join(kit, "holdout_guard.py")))
        self.assertEqual(holdout_kit.sha256_file(
            os.path.join(kit, "holdout_guard.py")),
            holdout_kit.sha256_file(os.path.join(TOOLS_DIR,
                                                 "holdout_guard.py")))
        holdout_kit.walk_regular(kit)  # raises on any symlink

    def test_eligible_repos_json(self):
        self.assertEqual(_load(os.path.join(self.F, "kit",
                                            "eligible-repos.json")),
                         {"repos": [os.path.realpath(self.repo)]})

    def test_final_line(self):
        out = io.StringIO()
        with mock.patch.object(sys, "stdout", out):
            holdout_kit.setup(os.path.join(self.tmp, "h2"), [self.repo],
                              skip_system_exclusions=True)
        lines = out.getvalue().splitlines()
        F2 = os.path.realpath(os.path.join(self.tmp, "h2"))
        self.assertTrue(all(ln.startswith(("OK: ", "PROBLEM: "))
                            for ln in lines))
        self.assertEqual(lines[-1], "OK: holdout folder ready at %s. "
                                    "Next: %s/bin/finder" % (F2, F2))

    def test_non_empty_folder_refused(self):
        folder = os.path.join(self.tmp, "busy")
        write(folder, "x", "x")
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.setup(folder, [self.repo],
                              skip_system_exclusions=True)
        self.assertIn("folder already exists and is not empty",
                      str(cm.exception))

    def test_existing_empty_folder_accepted(self):
        folder = os.path.join(self.tmp, "empty")
        os.makedirs(folder)
        with _quiet():
            holdout_kit.setup(folder, [self.repo],
                              skip_system_exclusions=True)
        self.assertTrue(os.path.isfile(os.path.join(folder, "bin", "finder")))

    def test_tuning_repo_refused_by_basename(self):
        for name in ("turingmind-code-review", "thejuran-marketplace"):
            parent = os.path.join(self.tmp, "p-" + name)
            os.makedirs(parent)
            repo = holdout_fixture.make_source_repo(parent, name)
            with self.assertRaises(holdout_kit.KitError) as cm:
                holdout_kit.setup(os.path.join(self.tmp, "h-" + name),
                                  [repo], skip_system_exclusions=True)
            self.assertIn(name, str(cm.exception))
            self.assertNotIn(parent, str(cm.exception))
            self.assertFalse(os.path.exists(os.path.join(self.tmp,
                                                         "h-" + name)))

    def test_b3_repo_accepted_with_note(self):
        repo = holdout_fixture.make_source_repo(self.tmp, "triggarr")
        out = io.StringIO()
        with mock.patch.object(sys, "stdout", out):
            holdout_kit.setup(os.path.join(self.tmp, "h3"), [repo],
                              skip_system_exclusions=True)
        self.assertIn("OK: triggarr (previously exposed during B3 "
                      "development; not eligible for C1/Q2)",
                      out.getvalue().splitlines())

    def test_non_git_repo_refused(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.setup(os.path.join(self.tmp, "h4"), [plain],
                              skip_system_exclusions=True)
        self.assertIn("not a git repository", str(cm.exception))

    def test_subdirs_name_no_generation_path(self):
        sd = holdout_kit.SUBDIRS
        self.assertNotIn("xcheck", sd)
        self.assertNotIn("cfg-xcheck", sd)
        self.assertNotIn("tmp/crosscheck/xcheck", sd)
        for rel in sd:
            self.assertFalse(holdout_kit.XCHECK_WS_RE.match(rel), rel)
            self.assertFalse(rel.startswith("cfg-xcheck"), rel)
            self.assertFalse(rel.startswith("tmp/crosscheck/xcheck"), rel)
            self.assertFalse(rel.startswith("bin/crosscheck"), rel)

    def test_fresh_setup_uses_real_workspace_helper(self):
        with mock.patch.object(holdout_kit, "make_xcheck_workspace",
                               wraps=holdout_kit.make_xcheck_workspace) as spy:
            F = self.inproc_setup("h5")
        self.assertEqual(spy.call_count, 1)
        args, kwargs = spy.call_args
        self.assertEqual(os.path.realpath(args[0]), F)
        self.assertEqual(args[1], 1)
        self.assertFalse(kwargs.get("prior"))
        self.assertTrue(os.path.isfile(os.path.join(F, "xcheck", ".claude",
                                                    "settings.json")))
        self.assertTrue(os.path.isfile(os.path.join(F, "xcheck",
                                                    "sandbox-probe.py")))
        self.assertEqual(os.listdir(os.path.join(F, "cfg-xcheck")), [])
        self.assertTrue(os.path.isfile(os.path.join(
            F, "tmp", "crosscheck", "xcheck", "SANDBOX-SENTINEL")))
        self.assertTrue(os.path.isfile(os.path.join(F, "bin", "crosscheck")))

    def test_mutant_subdirs_precreating_generation_path_breaks_setup(self):
        for extra in ("xcheck", "tmp/crosscheck/xcheck"):
            with mock.patch.object(holdout_kit, "SUBDIRS",
                                   holdout_kit.SUBDIRS + (extra,)):
                with self.assertRaises(holdout_kit.KitError) as cm, _quiet():
                    holdout_kit.setup(
                        os.path.join(self.tmp, "m-" + extra.replace("/", "_")),
                        [self.repo], skip_system_exclusions=True)
            self.assertEqual(str(cm.exception),
                             "cross-check workspace xcheck already exists")

    def test_tmutil_runs_unless_skipped(self):
        calls = []

        def fake(argv, **kw):
            calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 1, b"", b"")

        out = io.StringIO()
        with mock.patch.object(holdout_kit, "run_argv", side_effect=fake), \
                mock.patch.object(sys, "stdout", out):
            holdout_kit.setup(os.path.join(self.tmp, "h6"), [self.repo])
        F = os.path.realpath(os.path.join(self.tmp, "h6"))
        self.assertIn(["tmutil", "addexclusion", F], calls)
        self.assertTrue(any(ln.startswith("PROBLEM: ")
                            for ln in out.getvalue().splitlines()))
        self.assertTrue(out.getvalue().rstrip().endswith(
            "Next: %s/bin/finder" % F))

    def test_make_fake_holdout_layout(self):
        self.assertTrue(os.path.isdir(os.path.join(self.F, "work", ".claude")))
        self.assertTrue(os.path.isdir(os.path.join(self.repo, ".git")))
        self.assertEqual(os.path.basename(self.F), "holdout")


class TestTemplates(SetupCase):

    def test_templates_have_placeholders_and_only_tuning_paths(self):
        text = _read(os.path.join(KIT_DIR, "finder-settings.json"))
        self.assertIn("<H>/", text)
        for name in ("finder-settings.json", "crosscheck-settings.json"):
            t = _load(os.path.join(KIT_DIR, name))
            self.assertEqual(_deny_read(t), list(holdout_kit.TUNING_DENY_READ))
            self.assertNotIn("b3-ground-truth", _read(os.path.join(KIT_DIR,
                                                                   name)))
            self.assertFalse(any("--protect" == s for s in _strings(t)))

    def test_no_placeholder_survives(self):
        for path in (os.path.join(self.F, "work", ".claude", "settings.json"),
                     os.path.join(self.F, "xcheck", ".claude",
                                  "settings.json")):
            data = _load(path)
            for s in _strings(data):
                for tok in TOKENS:
                    self.assertNotIn(tok, s, path)

    def test_leftover_placeholder_refused(self):
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit._render_template({"a": ["<SEALED>/x"]}, self.F, [])
        self.assertEqual(holdout_kit._render_template(
            {"a": ["<REPOS>", "<H>/s"], "g": "<GUARD>"}, "/h", ["/r1", "/r2"]),
            {"a": ["/r1", "/r2", "/h/s"], "g": "/h/kit/holdout_guard.py"})

    def test_finder_settings(self):
        F, d = self.F, self.finder_settings()
        repo = os.path.realpath(self.repo)
        self.assertIs(d["autoMemoryEnabled"], False)
        perms = d["permissions"]
        self.assertIs(perms["blockReadsOutsideWorkingDirectories"], True)
        self.assertEqual(perms["additionalDirectories"],
                         [repo, F + "/sealed", F + "/kit"])
        for rule in ("Edit(%s/kit/**)" % F,
                     "Read(~/turingmind-code-review/**)",
                     "Read(~/thejuran-marketplace/**)", "Read(~/.claude/**)",
                     "Read(~/.codex/**)", "Read(~/.b3/**)",
                     "Read(~/.vibe-check-snapshots/**)",
                     "Edit(%s/**)" % repo,
                     "Read(%s/tmp/owner/**)" % F,
                     "Read(%s/tmp/crosscheck/**)" % F):
            self.assertIn(rule, perms["deny"])
        self.assertIs(d["sandbox"]["enabled"], True)
        self.assertIs(d["sandbox"]["failIfUnavailable"], True)
        self.assertEqual(set(_deny_read(d)),
                         set(holdout_kit.TUNING_DENY_READ)
                         | {F + "/tmp/owner", F + "/tmp/crosscheck"})
        self.assertNotIn(F + "/tmp/finder", _deny_read(d))
        self.assertNotIn(F + "/sealed", _deny_read(d))
        self.assertEqual(d["hooks"]["PreToolUse"][0]["matcher"], "*")
        self.assertEqual(_hook_args(d),
                         [F + "/kit/holdout_guard.py", "hook", "--role",
                          "finder", "--protect", F + "/tmp/owner",
                          "--protect", F + "/tmp/crosscheck"])

    def test_xcheck_gen1_settings(self):
        F, d = self.F, self.xcheck_settings()
        self.assertIs(d["autoMemoryEnabled"], False)
        self.assertNotIn("additionalDirectories", d["permissions"])
        for rule in ("Read(%s/sealed/**)" % F, "Read(%s/work/**)" % F,
                     "Read(%s/cfg-finder/**)" % F,
                     "Read(%s/kit/FINDER-BRIEF.md)" % F,
                     "Read(%s/tmp/finder/**)" % F,
                     "Read(%s/tmp/owner/**)" % F):
            self.assertIn(rule, d["permissions"]["deny"])
        args = _hook_args(d)
        self.assertEqual(args[-14:], [
            "--role", "xcheck", "--protect", F + "/sealed", "--protect",
            F + "/work", "--protect", F + "/cfg-finder", "--protect",
            F + "/kit/FINDER-BRIEF.md", "--protect", F + "/tmp/finder",
            "--protect", F + "/tmp/owner"])
        self.assertIs(d["sandbox"]["enabled"], True)
        self.assertIs(d["sandbox"]["failIfUnavailable"], True)
        self.assertEqual(set(_deny_read(d)),
                         set(holdout_kit.TUNING_DENY_READ)
                         | {F + "/sealed", F + "/work", F + "/cfg-finder",
                            F + "/kit/FINDER-BRIEF.md", F + "/tmp/finder",
                            F + "/tmp/owner"})
        self.assertFalse(any("tmp/crosscheck/xcheck" in s
                             for s in _strings(d)))


class TestFinderTmpIsolation(SetupCase):

    def test_written_settings_pass(self):
        self.assertEqual(holdout_kit.finder_settings_problems(
            self.finder_settings(), self.F), [])

    def test_missing_deny_read(self):
        d = self.finder_settings()
        _deny_read(d).remove(self.F + "/tmp/crosscheck")
        self.assertEqual(holdout_kit.finder_settings_problems(d, self.F),
                         ["sandbox denyRead is missing %s/tmp/crosscheck"
                          % self.F])

    def test_missing_protect(self):
        d = self.finder_settings()
        args = _hook_args(d)
        i = args.index(self.F + "/tmp/owner")
        del args[i - 1:i + 1]
        self.assertIn("hook --protect is missing %s/tmp/owner" % self.F,
                      holdout_kit.finder_settings_problems(d, self.F))

    def test_missing_permission_deny(self):
        d = self.finder_settings()
        d["permissions"]["deny"].remove("Read(%s/tmp/crosscheck/**)" % self.F)
        self.assertIn("permission deny is missing Read(%s/tmp/crosscheck/**)"
                      % self.F,
                      holdout_kit.finder_settings_problems(d, self.F))

    def test_kit_must_be_readable(self):
        d = self.finder_settings()
        d["permissions"]["additionalDirectories"].remove(self.F + "/kit")
        self.assertEqual(holdout_kit.finder_settings_problems(d, self.F),
                         ["additionalDirectories is missing %s/kit" % self.F])

    def test_sealed_must_be_readable(self):
        d = self.finder_settings()
        d["permissions"]["additionalDirectories"].remove(self.F + "/sealed")
        self.assertEqual(holdout_kit.finder_settings_problems(d, self.F),
                         ["additionalDirectories is missing %s/sealed"
                          % self.F])

    def test_kit_must_be_read_only(self):
        d = self.finder_settings()
        d["permissions"]["deny"].remove("Edit(%s/kit/**)" % self.F)
        self.assertEqual(holdout_kit.finder_settings_problems(d, self.F),
                         ["permission deny is missing Edit(%s/kit/**)"
                          % self.F])

    def test_kit_read_mutant_is_caught_by_setup(self):
        folder = os.path.join(self.tmp, "mk")
        real = holdout_kit._render_template

        def strip_kit(template, h, repos):
            out = real(template, h, repos)
            extra = out.get("permissions", {}).get("additionalDirectories")
            if isinstance(extra, list):
                extra[:] = [p for p in extra if not p.endswith("/kit")]
            return out

        with mock.patch.object(holdout_kit, "_render_template", strip_kit):
            with self.assertRaises(holdout_kit.KitError) as cm, _quiet():
                holdout_kit.setup(folder, [self.repo],
                                  skip_system_exclusions=True)
        self.assertIn("additionalDirectories is missing", str(cm.exception))

    def test_sandbox_flags(self):
        d = self.finder_settings()
        d["sandbox"]["enabled"] = False
        d["sandbox"]["failIfUnavailable"] = False
        probs = holdout_kit.finder_settings_problems(d, self.F)
        self.assertIn("sandbox is not enabled", probs)
        self.assertIn("sandbox does not fail if unavailable", probs)

    def test_mutant_a_stripped_writer_is_caught(self):
        folder = os.path.join(self.tmp, "ma")
        with mock.patch.object(holdout_kit, "_finder_protected_paths",
                               return_value=[]):
            with self.assertRaises(holdout_kit.KitError) as cm, _quiet():
                holdout_kit.setup(folder, [self.repo],
                                  skip_system_exclusions=True)
        F = os.path.realpath(folder)
        self.assertTrue(str(cm.exception).startswith(
            "finder settings failed their self-check: sandbox denyRead is "
            "missing %s/tmp/owner" % F))
        self.assertFalse(os.path.exists(os.path.join(F, "work", ".claude",
                                                     "settings.json")))

    def test_mutant_b_checker_is_what_blocks(self):
        folder = os.path.join(self.tmp, "mb")
        with mock.patch.object(holdout_kit, "_finder_protected_paths",
                               return_value=[]), \
                mock.patch.object(holdout_kit, "finder_settings_problems",
                                  return_value=[]), _quiet():
            holdout_kit.setup(folder, [self.repo],
                              skip_system_exclusions=True)
        F = os.path.realpath(folder)
        d = self.finder_settings(F)
        self.assertNotIn(F + "/tmp/owner", _deny_read(d))

    def test_guard_honors_finder_protects(self):
        F = self.F
        extra = [F + "/tmp/owner", F + "/tmp/crosscheck"]
        deny, _ = holdout_guard.classify(
            "Read", {"file_path": F + "/tmp/crosscheck/xcheck-r2/x"},
            role="finder", extra_protect=extra)
        self.assertTrue(deny)
        deny, _ = holdout_guard.classify(
            "Read", {"file_path": F + "/tmp/finder/x"}, role="finder",
            extra_protect=extra)
        self.assertFalse(deny)


class TestLaunchers(SetupCase):

    def _bin(self, name):
        return _read(os.path.join(self.F, "bin", name))

    def _common(self, text):
        lines = text.splitlines()
        self.assertEqual(lines[0], "#!/bin/bash")
        self.assertEqual(lines[1], "set -euo pipefail")
        self.assertIn(REFUSE_LINE, lines)
        self.assertNotIn('"$H/tmp"', text)

    def _tmp_exports(self, text):
        return (re.findall(r'CLAUDE_CODE_TMPDIR="([^"]*)"', text),
                re.findall(r'(?<![A-Z_])TMPDIR="([^"]*)"', text))

    def test_finder(self):
        t = self._bin("finder")
        self._common(t)
        for needle in ('export CLAUDE_CONFIG_DIR="$H/cfg-finder"',
                       "CLAUDE_CODE_PROJECT_DIR_NAME=finder",
                       "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
                       "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
                       'cd "$H/work"'):
            self.assertIn(needle, t)
        self.assertEqual(self._tmp_exports(t),
                         (["$H/tmp/finder"], ["$H/tmp/finder"]))
        self.assertEqual(t.rstrip().splitlines()[-1], 'exec claude "$@"')

    def test_crosscheck(self):
        t = self._bin("crosscheck")
        self._common(t)
        for needle in ('export CLAUDE_CONFIG_DIR="$H/cfg-xcheck"',
                       "CLAUDE_CODE_PROJECT_DIR_NAME=xcheck\n",
                       "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
                       "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
                       'cd "$H/xcheck"'):
            self.assertIn(needle, t)
        self.assertEqual(self._tmp_exports(t),
                         (["$H/tmp/crosscheck/xcheck"],
                          ["$H/tmp/crosscheck/xcheck"]))
        self.assertEqual(t.rstrip().splitlines()[-1], 'exec claude "$@"')

    def test_holdout(self):
        t = self._bin("holdout")
        self._common(t)
        self.assertEqual(self._tmp_exports(t), ([], ["$H/tmp/owner"]))
        self.assertEqual(t.rstrip().splitlines()[-1],
                         'exec python3 "$H/kit/tools/holdout_kit.py" '
                         '--folder "$H" "$@"')

    def test_h_is_baked_realpath(self):
        for name in ("finder", "crosscheck", "holdout"):
            self.assertIn("H='%s'" % self.F, self._bin(name).splitlines())

    def test_minted_generation_launcher(self):
        holdout_kit.make_xcheck_workspace(
            self.F, 2, prior=[holdout_kit.xcheck_names(1)])
        t = self._bin("crosscheck-r2")
        self._common(t)
        self.assertEqual(_mode(os.path.join(self.F, "bin", "crosscheck-r2")),
                         0o700)
        for needle in ('export CLAUDE_CONFIG_DIR="$H/cfg-xcheck-r2"',
                       "CLAUDE_CODE_PROJECT_DIR_NAME=xcheck-r2\n",
                       'cd "$H/xcheck-r2"'):
            self.assertIn(needle, t)
        self.assertEqual(self._tmp_exports(t),
                         (["$H/tmp/crosscheck/xcheck-r2"],
                          ["$H/tmp/crosscheck/xcheck-r2"]))

    def test_constants_never_export_shared_root(self):
        for const in (holdout_kit.FINDER_LAUNCHER,
                      holdout_kit.XCHECK_LAUNCHER,
                      holdout_kit.HOLDOUT_LAUNCHER):
            self.assertNotIn('"$H/tmp"', const)
            self.assertIn(REFUSE_LINE, const)
        with open(KIT_PY) as fh:
            src = [ln for ln in fh if not ln.startswith("#")]
        self.assertFalse(any('"$H/tmp"' in ln for ln in src))

    def test_finder_refuses_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = subprocess.run([os.path.join(self.F, "bin", "finder")],
                              env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=60)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Open a new Terminal window (not one started by "
                      "Claude) and run this again.", proc.stdout)

    def test_holdout_launcher_help(self):
        proc = subprocess.run([os.path.join(self.F, "bin", "holdout"),
                               "--help"], env=holdout_fixture.kit_env(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("setup", proc.stdout)

    def test_folder_with_quote_still_launches(self):
        folder = os.path.join(self.tmp, "it's here")
        with _quiet():
            holdout_kit.setup(folder, [self.repo],
                              skip_system_exclusions=True)
        proc = subprocess.run([os.path.join(folder, "bin", "holdout"),
                               "--help"], env=holdout_fixture.kit_env(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestXcheckWorkspace(SetupCase):

    def test_names(self):
        self.assertEqual(holdout_kit.xcheck_names(1), {
            "workspace": "xcheck", "config_dir": "cfg-xcheck",
            "tmp_dir": "tmp/crosscheck/xcheck", "launcher": "bin/crosscheck"})
        self.assertEqual(holdout_kit.xcheck_names(3), {
            "workspace": "xcheck-r3", "config_dir": "cfg-xcheck-r3",
            "tmp_dir": "tmp/crosscheck/xcheck-r3",
            "launcher": "bin/crosscheck-r3"})
        for bad in (0, -1, True, "2"):
            with self.assertRaises(holdout_kit.KitError):
                holdout_kit.xcheck_names(bad)
        self.assertTrue(holdout_kit.XCHECK_WS_RE.match("xcheck"))
        self.assertTrue(holdout_kit.XCHECK_WS_RE.match("xcheck-r12"))
        self.assertFalse(holdout_kit.XCHECK_WS_RE.match("xcheck-r1"))

    def test_mint_gen2(self):
        F = self.F
        names = holdout_kit.make_xcheck_workspace(
            F, 2, prior=[holdout_kit.xcheck_names(1)])
        self.assertEqual(names, holdout_kit.xcheck_names(2))
        d = self.xcheck_settings("xcheck-r2")
        self.assertEqual(os.listdir(os.path.join(F, "cfg-xcheck-r2")), [])
        self.assertEqual(_mode(os.path.join(F, "bin", "crosscheck-r2")),
                         0o700)
        tmp2 = os.path.join(F, "tmp", "crosscheck", "xcheck-r2")
        self.assertEqual(_mode(tmp2), 0o700)
        self.assertEqual(os.listdir(tmp2), ["SANDBOX-SENTINEL"])
        expected = holdout_kit._xcheck_protected_paths(
            F, [holdout_kit.xcheck_names(1)])
        prior_paths = [F + "/xcheck", F + "/cfg-xcheck",
                       F + "/tmp/crosscheck/xcheck"]
        self.assertEqual(expected[-3:], prior_paths)
        deny = d["permissions"]["deny"]
        protects = _protects(_hook_args(d))
        for p in expected:
            rule = ("Read(%s)" % p if p.endswith("FINDER-BRIEF.md")
                    else "Read(%s/**)" % p)
            self.assertIn(rule, deny)
            self.assertIn(p, protects)
            self.assertIn(p, _deny_read(d))
        self.assertEqual(protects, expected)
        self.assertNotIn(F + "/tmp/crosscheck/xcheck-r2", _deny_read(d))

    def test_mint_gen3_covers_both_earlier_generations(self):
        F = self.F
        n1, n2 = holdout_kit.xcheck_names(1), holdout_kit.xcheck_names(2)
        holdout_kit.make_xcheck_workspace(F, 2, prior=[n1])
        holdout_kit.make_xcheck_workspace(F, 3, prior=[n1, n2])
        d = self.xcheck_settings("xcheck-r3")
        protects = _protects(_hook_args(d))
        for n in (n1, n2):
            for key in ("workspace", "config_dir", "tmp_dir"):
                p = F + "/" + n[key]
                self.assertIn("Read(%s/**)" % p, d["permissions"]["deny"])
                self.assertIn(p, protects)
                self.assertIn(p, _deny_read(d))

    def test_second_mint_refused(self):
        prior = [holdout_kit.xcheck_names(1)]
        holdout_kit.make_xcheck_workspace(self.F, 2, prior=prior)
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.make_xcheck_workspace(self.F, 2, prior=prior)
        self.assertEqual(str(cm.exception),
                         "cross-check workspace xcheck-r2 already exists")

    def test_stray_tmp_root_alone_refuses(self):
        os.makedirs(os.path.join(self.F, "tmp", "crosscheck", "xcheck-r3"))
        with self.assertRaises(holdout_kit.KitError) as cm:
            holdout_kit.make_xcheck_workspace(
                self.F, 3, prior=[holdout_kit.xcheck_names(1),
                                  holdout_kit.xcheck_names(2)])
        self.assertEqual(str(cm.exception),
                         "cross-check workspace xcheck-r3 already exists")

    def test_incomplete_prior_refused(self):
        with self.assertRaises(holdout_kit.KitError):
            holdout_kit.make_xcheck_workspace(self.F, 3, prior=[
                holdout_kit.xcheck_names(1)])
        self.assertFalse(os.path.exists(os.path.join(self.F, "xcheck-r3")))

    def test_older_generation_never_rewritten(self):
        path = os.path.join(self.F, "xcheck", ".claude", "settings.json")
        with open(path, "rb") as fh:
            before = fh.read()
        holdout_kit.make_xcheck_workspace(
            self.F, 2, prior=[holdout_kit.xcheck_names(1)])
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), before)

    def test_guard_honors_xcheck_protects(self):
        F = self.F
        deny, _ = holdout_guard.classify(
            "Read", {"file_path": F + "/xcheck/X-1/blind.json"},
            role="xcheck", extra_protect=[F + "/xcheck", F + "/cfg-xcheck",
                                          F + "/tmp/crosscheck/xcheck"])
        self.assertTrue(deny)
        deny, _ = holdout_guard.classify(
            "Read", {"file_path": F + "/tmp/finder/scratch.txt"},
            role="xcheck", extra_protect=[F + "/tmp/finder"])
        self.assertTrue(deny)


class TestXcheckSandbox(SetupCase):

    def _gen3(self):
        n1, n2 = holdout_kit.xcheck_names(1), holdout_kit.xcheck_names(2)
        holdout_kit.make_xcheck_workspace(self.F, 2, prior=[n1])
        holdout_kit.make_xcheck_workspace(self.F, 3, prior=[n1, n2])
        return [n1, n2]

    def test_written_settings_pass(self):
        self.assertEqual(holdout_kit.xcheck_settings_problems(
            self.xcheck_settings(), self.F), [])
        prior = self._gen3()
        self.assertEqual(holdout_kit.xcheck_settings_problems(
            self.xcheck_settings("xcheck-r3"), self.F, prior), [])

    def test_missing_sealed(self):
        d = self.xcheck_settings()
        _deny_read(d).remove(self.F + "/sealed")
        self.assertEqual(holdout_kit.xcheck_settings_problems(d, self.F),
                         ["sandbox denyRead is missing %s/sealed" % self.F])

    def test_missing_prior_workspace(self):
        prior = self._gen3()
        d = self.xcheck_settings("xcheck-r3")
        _deny_read(d).remove(self.F + "/xcheck-r2")
        self.assertIn("sandbox denyRead is missing %s/xcheck-r2" % self.F,
                      holdout_kit.xcheck_settings_problems(d, self.F, prior))

    def test_sandbox_flags(self):
        d = self.xcheck_settings()
        d["sandbox"]["enabled"] = False
        self.assertIn("sandbox is not enabled",
                      holdout_kit.xcheck_settings_problems(d, self.F))
        d = self.xcheck_settings()
        d["sandbox"]["failIfUnavailable"] = False
        self.assertIn("sandbox does not fail if unavailable",
                      holdout_kit.xcheck_settings_problems(d, self.F))

    def test_missing_protect_and_deny(self):
        prior = [holdout_kit.xcheck_names(1)]
        holdout_kit.make_xcheck_workspace(self.F, 2, prior=prior)
        d = self.xcheck_settings("xcheck-r2")
        args = _hook_args(d)
        i = args.index(self.F + "/cfg-xcheck")
        del args[i - 1:i + 1]
        self.assertIn("hook --protect is missing %s/cfg-xcheck" % self.F,
                      holdout_kit.xcheck_settings_problems(d, self.F, prior))
        d = self.xcheck_settings()
        d["permissions"]["deny"].remove("Read(%s/work/**)" % self.F)
        self.assertIn("permission deny is missing Read(%s/work/**)" % self.F,
                      holdout_kit.xcheck_settings_problems(d, self.F))

    def test_tmp_roots(self):
        d = self.xcheck_settings()
        _deny_read(d).remove(self.F + "/tmp/owner")
        self.assertEqual(holdout_kit.xcheck_settings_problems(d, self.F),
                         ["sandbox denyRead is missing %s/tmp/owner" % self.F])
        prior = [holdout_kit.xcheck_names(1)]
        holdout_kit.make_xcheck_workspace(self.F, 2, prior=prior)
        d = self.xcheck_settings("xcheck-r2")
        args = _hook_args(d)
        i = args.index(self.F + "/tmp/crosscheck/xcheck")
        del args[i - 1:i + 1]
        self.assertIn("hook --protect is missing %s/tmp/crosscheck/xcheck"
                      % self.F,
                      holdout_kit.xcheck_settings_problems(d, self.F, prior))
        d = self.xcheck_settings()
        d["permissions"]["deny"].remove("Read(%s/tmp/finder/**)" % self.F)
        self.assertIn("permission deny is missing Read(%s/tmp/finder/**)"
                      % self.F,
                      holdout_kit.xcheck_settings_problems(d, self.F))

    def _gone(self, F, names):
        for key in ("workspace", "config_dir", "tmp_dir", "launcher"):
            self.assertFalse(os.path.lexists(os.path.join(F, names[key])),
                             names[key])

    def test_mutant_1_stripped_writer_fails_closed(self):
        F2 = self.inproc_setup("h2")
        self.strip_gen1(F2)
        with mock.patch.object(holdout_kit, "_xcheck_protected_paths",
                               return_value=[]):
            with self.assertRaises(holdout_kit.KitError) as cm:
                holdout_kit.make_xcheck_workspace(F2, 1)
        self.assertTrue(str(cm.exception).startswith(
            "cross-check settings failed their self-check: sandbox denyRead "
            "is missing"))
        self._gone(F2, holdout_kit.xcheck_names(1))

    def test_mutant_3_tmp_roots_in_checker_expectation(self):
        F4 = self.inproc_setup("h4")
        self.strip_gen1(F4)
        real = holdout_kit._xcheck_protected_paths

        def stripped(folder, prior=()):
            return [p for p in real(folder, prior)
                    if not p.startswith(F4 + "/tmp/")]

        with mock.patch.object(holdout_kit, "_xcheck_protected_paths",
                               side_effect=stripped):
            with self.assertRaises(holdout_kit.KitError) as cm:
                holdout_kit.make_xcheck_workspace(F4, 1)
            self.assertEqual(
                str(cm.exception),
                "cross-check settings failed their self-check: sandbox "
                "denyRead is missing %s/tmp/finder" % F4)
            self._gone(F4, holdout_kit.xcheck_names(1))
        # Restore a real generation 1, then mint generation 2 stripped.
        holdout_kit.make_xcheck_workspace(F4, 1)
        with mock.patch.object(holdout_kit, "_xcheck_protected_paths",
                               side_effect=stripped), \
                mock.patch.object(holdout_kit, "xcheck_settings_problems",
                                  wraps=holdout_kit.xcheck_settings_problems
                                  ) as spy:
            with self.assertRaises(holdout_kit.KitError):
                holdout_kit.make_xcheck_workspace(
                    F4, 2, prior=[holdout_kit.xcheck_names(1)])
        settings, folder, prior = spy.call_args[0]
        problems = holdout_kit.xcheck_settings_problems(settings, folder,
                                                        prior)
        self.assertIn("sandbox denyRead is missing %s/tmp/crosscheck/xcheck"
                      % F4, problems)
        self._gone(F4, holdout_kit.xcheck_names(2))

    def test_mutant_2_checker_is_what_blocks(self):
        F3 = self.inproc_setup("h3")
        self.strip_gen1(F3)
        with mock.patch.object(holdout_kit, "_xcheck_protected_paths",
                               return_value=[]), \
                mock.patch.object(holdout_kit, "xcheck_settings_problems",
                                  return_value=[]):
            holdout_kit.make_xcheck_workspace(F3, 1)
        d = self.xcheck_settings(F=F3)
        self.assertNotIn(F3 + "/sealed", _deny_read(d))


class TestSandboxProbe(SetupCase):

    def _probe(self, ws="xcheck"):
        return os.path.join(self.F, ws, "sandbox-probe.py")

    def _targets(self, ws="xcheck"):
        tree = ast.parse(_read(self._probe(ws)))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                    getattr(t, "id", None) == "TARGETS" for t in node.targets):
                return ast.literal_eval(node.value)
        self.fail("no TARGETS")

    def test_gen1_targets(self):
        F = self.F
        self.assertEqual(_mode(self._probe()), 0o700)
        self.assertEqual(self._targets(), [
            F + "/sealed/SANDBOX-SENTINEL", F + "/work", F + "/cfg-finder",
            F + "/kit/FINDER-BRIEF.md", F + "/tmp/finder/SANDBOX-SENTINEL",
            F + "/tmp/owner/SANDBOX-SENTINEL"])

    def test_gen3_targets(self):
        F = self.F
        n1, n2 = holdout_kit.xcheck_names(1), holdout_kit.xcheck_names(2)
        holdout_kit.make_xcheck_workspace(F, 2, prior=[n1])
        holdout_kit.make_xcheck_workspace(F, 3, prior=[n1, n2])
        t = self._targets("xcheck-r3")
        self.assertEqual(len(t), 12)
        self.assertEqual(t[6:], [
            F + "/xcheck/.claude/settings.json", F + "/cfg-xcheck",
            F + "/tmp/crosscheck/xcheck/SANDBOX-SENTINEL",
            F + "/xcheck-r2/.claude/settings.json", F + "/cfg-xcheck-r2",
            F + "/tmp/crosscheck/xcheck-r2/SANDBOX-SENTINEL"])
        self.assertFalse(any("xcheck-r3" in p for p in t))

    def test_prints_only_fixed_lines(self):
        tree = ast.parse(_read(self._probe()))
        prints = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and getattr(n.func, "id", None) == "print"]
        self.assertEqual(len(prints), 2)
        for call in prints:
            for arg in call.args:
                self.assertNotIsInstance(arg, ast.Name)
        self.assertEqual(_imports(tree), {"errno", "os", "sys"})

    def test_unsandboxed_run_reports_problem(self):
        proc = subprocess.run([sys.executable, self._probe()],
                              cwd=os.path.join(self.F, "xcheck"),
                              env=holdout_fixture.kit_env(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout,
                         "PROBLEM: sandbox did not deny 6 of 6 protected "
                         "reads. Stop. Do not type begin. Close this session "
                         "and reply: blocked sandbox\n")
        self.assertEqual(proc.stderr, "")
        self.assertNotIn(holdout_kit.SANDBOX_SENTINEL_TEXT.strip(),
                         proc.stdout + proc.stderr)
        self.assertNotIn("sentinel", (proc.stdout + proc.stderr).lower())

    def _inproc(self, exc):
        out = io.StringIO()
        with mock.patch("os.open", side_effect=exc), \
                mock.patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                runpy.run_path(self._probe(), run_name="__main__")
        return cm.exception.code, out.getvalue()

    def test_denied_reads_pass(self):
        code, out = self._inproc(PermissionError(errno.EACCES, "x"))
        self.assertEqual(code, 0)
        self.assertEqual(out, "OK: sandbox denied 6/6 protected reads\n")
        code, out = self._inproc(PermissionError(errno.EPERM, "x"))
        self.assertEqual(code, 0)

    def test_missing_target_is_not_a_pass(self):
        code, out = self._inproc(FileNotFoundError(errno.ENOENT, "x"))
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("PROBLEM: sandbox did not deny 6 of 6"))
        self.assertNotIn(self.F, out)


class TestKitInventory(SetupCase):

    def test_inventory(self):
        kit = os.path.join(self.F, "kit")
        inv = _load(os.path.join(kit, "KIT-INVENTORY.json"))
        self.assertEqual(inv["schema"], "vibe-check-holdout-kit-inventory/1")
        expected = set(holdout_kit.walk_regular(kit)) - {
            "KIT-INVENTORY.json", "eligible-repos.json"}
        self.assertEqual(set(inv["files"]), expected)
        self.assertIn("tools/holdout_kit.py", inv["files"])
        self.assertIn("holdout_guard.py", inv["files"])
        self.assertNotIn("eligible-repos.json", inv["files"])
        for rel, digest in inv["files"].items():
            self.assertEqual(holdout_kit.sha256_file(os.path.join(kit, rel)),
                             digest, rel)
        target = os.path.join(kit, "tools", "holdout_kit.py")
        with open(target, "ab") as fh:
            fh.write(b"#")
        self.assertNotEqual(holdout_kit.sha256_file(target),
                            inv["files"]["tools/holdout_kit.py"])


class TestB3Exclusions(unittest.TestCase):
    """D-13: the B3-exposed repo set plus dashboard (owner decision), the
    tuning repo and its mirror excluded from every slot, and content hashes
    of every B3 commit id and patch. Only the source_repo/base_sha/feature_sha
    lines of the provenance files are read; nothing is printed."""

    def setUp(self):
        self.data = _load(os.path.join(KIT_DIR, "b3-exclusions.json"))
        self.prov = sorted(glob.glob(os.path.join(B3_DIFFS, "*.provenance")))
        self.patches = sorted(glob.glob(os.path.join(B3_DIFFS, "*.patch")))
        self.assertTrue(self.prov)
        self.assertTrue(self.patches)

    def _fields(self, prefix):
        out = []
        for path in self.prov:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith(prefix):
                        out.append(line.split(":", 1)[1].strip())
        return out

    def test_shape(self):
        self.assertEqual(set(self.data), {
            "schema", "repos", "exclude_all_slots", "commit_sha256",
            "patch_sha256", "note"})
        self.assertEqual(self.data["schema"],
                         "vibe-check-holdout-b3-exclusions/1")

    def test_repos_cover_provenance_plus_dashboard(self):
        derived = {os.path.basename(os.path.expanduser(v).rstrip("/"))
                   for v in self._fields("source_repo:")}
        self.assertTrue(derived)
        self.assertTrue(set(self.data["repos"]) >= derived | {"dashboard"})
        self.assertEqual(self.data["exclude_all_slots"],
                         ["thejuran-marketplace", "turingmind-code-review"])
        self.assertIn("previously exposed during B3 development",
                      self.data["note"])

    def test_commit_hashes(self):
        shas = self._fields("base_sha:") + self._fields("feature_sha:")
        self.assertTrue(shas)
        expected = sorted({hashlib.sha256(s.encode()).hexdigest()
                           for s in shas})
        self.assertEqual(self.data["commit_sha256"], expected)

    def test_patch_hashes(self):
        expected = []
        for p in self.patches:
            with open(p, "rb") as fh:
                expected.append(hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(self.data["patch_sha256"], sorted(set(expected)))
        self.assertEqual(len(self.data["patch_sha256"]), len(self.patches))


if __name__ == "__main__":
    unittest.main()
