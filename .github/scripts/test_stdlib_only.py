"""Tests for stdlib_only.py, the CI stdlib-only import gate.

Every rule the gate enforces has a mutant that trips it: a planted
third-party import in a plain module and in gitfixture.py exits 1, a plant in
a test_*.py file does not (test files are out of scope), and empty, missing or
broken input exits 2. Each mutant first shows the unmutated tree passes and
that the planted text really changed the file.
"""

import ast
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stdlib_only  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
STDLIB_ONLY_PY = os.path.join(HERE, "stdlib_only.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugins", "vibe-check")

PLANT_REQUESTS = "import requests\n"
PLANT_YAML = "from yaml import safe_load\n"


def run_main(argv):
    """Call main() and capture what it prints."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = stdlib_only.main(argv)
    return code, out.getvalue(), err.getvalue()


class TreeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, rel, text):
        path = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def read(self, rel):
        with open(os.path.join(self.tmp, rel), encoding="utf-8") as fh:
            return fh.read()

    def plant(self, rel, line):
        """Append a planted import and assert the file really changed."""
        before = self.read(rel)
        self.write(rel, before + line)
        after = self.read(rel)
        self.assertNotEqual(after, before)
        self.assertIn(line.strip(), after)

    def good_tree(self):
        self.write("a.py", "import json\nimport b\n")
        self.write("b.py", "import os\n")


class TestRealTree(unittest.TestCase):
    def _independent_count(self):
        proc = subprocess.run(["git", "-C", REPO_ROOT, "ls-files", "plugins/vibe-check/*.py"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60, check=True)
        names = [p for p in proc.stdout.splitlines() if p.strip()]
        return len([p for p in names if not os.path.basename(p).startswith("test_")])

    def test_real_tree_is_clean_with_independent_count(self):
        expected = self._independent_count()
        self.assertEqual(expected, 34)
        files, bad = stdlib_only.scan(PLUGIN_ROOT)
        self.assertEqual(bad, {})
        self.assertEqual(len(files), expected)
        self.assertIn(os.path.join("scripts", "gitfixture.py"), files)
        code, out, _err = run_main([PLUGIN_ROOT])
        self.assertEqual(code, 0)
        self.assertIn("%d shipped .py files; third-party imports: none" % expected, out)

    def test_real_tree_cli_isolated(self):
        proc = subprocess.run([sys.executable, "-I", STDLIB_ONLY_PY, PLUGIN_ROOT],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "34 shipped .py files; third-party imports: none")


class TestTempTrees(TreeCase):
    def test_good_tree_passes(self):
        self.good_tree()
        code, out, _err = run_main([self.tmp])
        self.assertEqual(code, 0)
        self.assertIn("2 shipped .py files; third-party imports: none", out)

    def test_planted_import_in_plain_module_trips(self):
        self.good_tree()
        self.assertEqual(run_main([self.tmp])[0], 0)
        self.plant("a.py", PLANT_REQUESTS)
        code, out, err = run_main([self.tmp])
        self.assertEqual(code, 1)
        text = out + err
        self.assertIn("THIRD-PARTY IMPORT FOUND — STOPPING", text)
        self.assertIn("a.py: requests", text)

    def test_planted_import_in_gitfixture_trips(self):
        self.good_tree()
        self.write("scripts/gitfixture.py", "import subprocess\n")
        self.assertEqual(run_main([self.tmp])[0], 0)
        self.plant("scripts/gitfixture.py", PLANT_YAML)
        code, out, err = run_main([self.tmp])
        self.assertEqual(code, 1)
        self.assertIn("gitfixture.py: yaml", out + err)

    def test_planted_import_in_test_file_is_out_of_scope(self):
        self.good_tree()
        self.write("test_x.py", "import unittest\n")
        self.assertEqual(run_main([self.tmp])[0], 0)
        self.plant("test_x.py", PLANT_REQUESTS)
        code, out, _err = run_main([self.tmp])
        self.assertEqual(code, 0)
        self.assertIn("2 shipped .py files", out)

    def test_relative_and_dotted_stdlib_imports_pass(self):
        self.good_tree()
        self.write("c.py", "from . import b\nimport os.path\nfrom xml.etree import ElementTree\n")
        self.assertEqual(run_main([self.tmp])[0], 0)

    def test_sibling_in_subdirectory_counts_as_local(self):
        self.write("pkg/helper.py", "import os\n")
        self.write("a.py", "import helper\n")
        self.assertEqual(run_main([self.tmp])[0], 0)

    def test_pycache_is_skipped(self):
        self.good_tree()
        self.write("__pycache__/junk.py", PLANT_REQUESTS)
        code, out, _err = run_main([self.tmp])
        self.assertEqual(code, 0)
        self.assertIn("2 shipped .py files", out)


class TestUnusableInput(TreeCase):
    def test_empty_directory_exits_2(self):
        code, out, err = run_main([self.tmp])
        self.assertEqual(code, 2)
        self.assertIn("NO SHIPPED .py FILES FOUND", err)
        self.assertIn("— STOPPING", err)

    def test_only_test_files_exits_2(self):
        self.write("test_only.py", "import os\n")
        code, _out, err = run_main([self.tmp])
        self.assertEqual(code, 2)
        self.assertIn("NO SHIPPED .py FILES FOUND", err)

    def test_missing_directory_exits_2(self):
        code, _out, err = run_main([os.path.join(self.tmp, "nope")])
        self.assertEqual(code, 2)
        self.assertIn("— STOPPING", err)

    def test_no_argument_exits_2(self):
        code, _out, err = run_main([])
        self.assertEqual(code, 2)
        self.assertIn("usage", err.lower())
        self.assertIn("— STOPPING", err)

    def test_extra_argument_exits_2(self):
        self.good_tree()
        code, _out, err = run_main([self.tmp, self.tmp])
        self.assertEqual(code, 2)
        self.assertIn("— STOPPING", err)

    def test_syntax_error_exits_2_and_names_file(self):
        self.good_tree()
        self.assertEqual(run_main([self.tmp])[0], 0)
        self.write("broken.py", "def (:\n")
        code, out, err = run_main([self.tmp])
        self.assertEqual(code, 2)
        self.assertIn("broken.py", err)
        self.assertIn("— STOPPING", err)
        self.assertNotIn("third-party imports: none", out)

    def test_undecodable_file_exits_2_and_names_file(self):
        self.good_tree()
        with open(os.path.join(self.tmp, "binary.py"), "wb") as fh:
            fh.write(b"\xff\xfe\x00bad")
        code, _out, err = run_main([self.tmp])
        self.assertEqual(code, 2)
        self.assertIn("binary.py", err)

    def test_nonexistent_cli_exits_2(self):
        proc = subprocess.run([sys.executable, "-I", STDLIB_ONLY_PY, "/nonexistent"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(any(line.endswith("— STOPPING")
                            for line in proc.stderr.splitlines()), proc.stderr)


class TestCliMatchesMain(TreeCase):
    def _cli(self, *argv):
        return subprocess.run([sys.executable, "-I", STDLIB_ONLY_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)

    def test_exit_codes_match(self):
        self.good_tree()
        self.assertEqual(self._cli(self.tmp).returncode, run_main([self.tmp])[0])
        self.assertEqual(self._cli(self.tmp).returncode, 0)
        self.plant("a.py", PLANT_REQUESTS)
        self.assertEqual(self._cli(self.tmp).returncode, run_main([self.tmp])[0])
        self.assertEqual(self._cli(self.tmp).returncode, 1)
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        self.assertEqual(self._cli(empty).returncode, run_main([empty])[0])
        self.assertEqual(self._cli(empty).returncode, 2)


class _AcceptEverything(frozenset):
    def __contains__(self, item):
        return True


class TestMutants(TreeCase):
    def test_allowed_set_comparison_is_load_bearing(self):
        self.good_tree()
        self.plant("a.py", PLANT_REQUESTS)
        self.assertEqual(run_main([self.tmp])[0], 1)
        with mock.patch.object(stdlib_only, "stdlib_names",
                               return_value=_AcceptEverything()):
            code, _out, _err = run_main([self.tmp])
        # With the allowed set widened to everything, the planted import no
        # longer trips: the comparison against the stdlib names is the guard.
        self.assertEqual(code, 0)


class TestImportSet(unittest.TestCase):
    def test_module_level_imports(self):
        with open(STDLIB_ONLY_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertEqual(names, {"ast", "os", "sys"})

    def test_every_subprocess_run_in_tests_has_timeout(self):
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "run"
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
        self.assertTrue(calls)
        for c in calls:
            self.assertIn("timeout", {k.arg for k in c.keywords})


if __name__ == "__main__":
    unittest.main()
