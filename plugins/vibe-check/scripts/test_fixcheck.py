"""Tests for fixcheck.py — the fix agent's allowlisted check picker and runner.

Fixture trees live in a TemporaryDirectory. Runners are tiny `#!/bin/sh`
scripts (chmod 0755) under `.venv/bin/`, `node_modules/.bin/` or a private
PATH directory, and PATH is pinned per test so the host's real pytest/node/go
never leak into a pick.
"""

import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixcheck  # noqa: E402


def write(path, text, mode=None):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    if mode is not None:
        os.chmod(path, mode)


def fake_exe(path, body="exit 0\n"):
    write(path, "#!/bin/sh\n" + body, 0o755)


class TreeCase(unittest.TestCase):
    """A fixture repo root plus an isolated PATH directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)
        self.repo = os.path.join(self.root, "repo")
        self.bindir = os.path.join(self.root, "pathbin")
        os.makedirs(self.repo)
        os.makedirs(self.bindir)
        self._env = mock.patch.dict(os.environ, {"PATH": self.bindir})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def r(self, rel, text="x = 1\n", mode=None):
        write(os.path.join(self.repo, rel), text, mode)

    def on_path(self, name, body="exit 0\n"):
        fake_exe(os.path.join(self.bindir, name), body)

    def local(self, rel, body="exit 0\n"):
        fake_exe(os.path.join(self.repo, rel), body)

    def pick(self, path):
        return fixcheck.pick_checks(self.repo, path)

    def kinds(self, path):
        return [c["kind"] for c in self.pick(path)]


def all_argv_words(cands):
    words = []
    for c in cands:
        words.extend(c.get("argv") or [])
    return words


class TestPickPython(TreeCase):

    def test_sibling_test_with_venv_runner_is_first(self):
        self.r("pkg/mod.py")
        self.r("pkg/test_mod.py")
        self.local(".venv/bin/pytest")
        self.on_path("pytest")  # the repo venv still wins
        cands = self.pick("pkg/mod.py")
        self.assertEqual(cands[0]["kind"], "test")
        self.assertEqual(cands[0]["argv"], [
            os.path.join(self.repo, ".venv/bin/pytest"), "-q", "-x", "-p",
            "no:cacheprovider", "pkg/test_mod.py"])
        self.assertEqual(cands[-1]["kind"], "syntax")
        self.assertEqual(cands[-1]["inproc"], "ast")
        self.assertIsNone(cands[-1]["argv"])
        self.assertEqual(cands[-1]["display"], "python ast parse")

    def test_path_pytest_when_no_venv(self):
        self.r("mod.py")
        self.r("mod_test.py")
        self.on_path("pytest")
        cands = self.pick("mod.py")
        self.assertEqual(cands[0]["argv"][0], "pytest")
        self.assertEqual(cands[0]["argv"][-1], "mod_test.py")

    def test_non_executable_venv_runner_falls_to_path(self):
        self.r("mod.py")
        self.r("test_mod.py")
        write(os.path.join(self.repo, ".venv/bin/pytest"), "#!/bin/sh\n", 0o644)
        self.on_path("pytest")
        self.assertEqual(self.pick("mod.py")[0]["argv"][0], "pytest")

    def test_no_runner_means_no_test_candidate(self):
        self.r("mod.py")
        self.r("test_mod.py")
        self.assertEqual(self.kinds("mod.py"), ["syntax"])

    def test_test_file_runs_itself(self):
        self.r("pkg/test_thing.py")
        self.on_path("pytest")
        cands = self.pick("pkg/test_thing.py")
        self.assertEqual(cands[0]["kind"], "test")
        self.assertEqual(cands[0]["argv"][-1], "pkg/test_thing.py")

    def test_tests_dir_found_walking_up(self):
        self.r("src/deep/mod.py")
        self.r("tests/test_mod.py")
        self.on_path("pytest")
        cands = self.pick("src/deep/mod.py")
        self.assertEqual(cands[0]["kind"], "test")
        self.assertEqual(cands[0]["argv"][-1], "tests/test_mod.py")

    def test_no_test_file_means_syntax_only(self):
        self.r("mod.py")
        self.on_path("pytest")
        self.assertEqual(self.kinds("mod.py"), ["syntax"])

    def test_ruff_needs_path_and_config(self):
        self.r("mod.py")
        self.on_path("ruff")
        self.assertEqual(self.kinds("mod.py"), ["syntax"])
        self.r("pyproject.toml", "[tool.ruff]\nline-length = 100\n")
        cands = self.pick("mod.py")
        self.assertEqual([c["kind"] for c in cands], ["lint", "syntax"])
        self.assertEqual(cands[0]["argv"], ["ruff", "check", "mod.py"])

    def test_ruff_config_without_ruff_on_path(self):
        self.r("mod.py")
        self.r("ruff.toml", "")
        self.assertEqual(self.kinds("mod.py"), ["syntax"])

    def test_flake8_needs_path_and_config(self):
        self.r("mod.py")
        self.on_path("flake8")
        self.r("setup.cfg", "[metadata]\nname = x\n")
        self.assertEqual(self.kinds("mod.py"), ["syntax"])
        self.r("setup.cfg", "[flake8]\nmax-line-length = 100\n")
        cands = self.pick("mod.py")
        self.assertEqual(cands[0]["argv"], ["flake8", "mod.py"])


class TestPickJs(TreeCase):

    def test_sibling_test_with_local_vitest(self):
        self.r("src/a.ts", "export const a = 1\n")
        self.r("src/a.test.ts", "")
        self.local("node_modules/.bin/vitest")
        cands = self.pick("src/a.ts")
        self.assertEqual(cands[0]["kind"], "test")
        self.assertEqual(cands[0]["argv"], [
            os.path.join(self.repo, "node_modules/.bin/vitest"), "run",
            "src/a.test.ts"])
        self.assertEqual(cands[0]["display"],
                         "node_modules/.bin/vitest run src/a.test.ts")

    def test_spec_and_jest(self):
        self.r("src/b.js")
        self.r("src/b.spec.js")
        self.local("node_modules/.bin/jest")
        cands = self.pick("src/b.js")
        self.assertEqual(cands[0]["argv"], [
            os.path.join(self.repo, "node_modules/.bin/jest"), "src/b.spec.js"])

    def test_dunder_tests_dir(self):
        self.r("src/c.jsx")
        self.r("src/__tests__/c.jsx")
        self.local("node_modules/.bin/jest")
        self.assertEqual(self.pick("src/c.jsx")[0]["argv"][-1],
                         "src/__tests__/c.jsx")

    def test_no_local_runner_means_no_test_even_with_npx_on_path(self):
        self.r("src/a.ts")
        self.r("src/a.test.ts")
        self.on_path("npx")
        self.on_path("vitest")  # a PATH vitest is not repo-local: ignored
        self.assertEqual(self.kinds("src/a.ts"), [])

    def test_tsc_with_nearest_tsconfig(self):
        self.r("tsconfig.json", "{}")
        self.r("pkg/web/tsconfig.json", "{}")
        self.r("pkg/web/src/x.tsx")
        self.local("node_modules/.bin/tsc")
        cands = self.pick("pkg/web/src/x.tsx")
        self.assertEqual(cands[0]["kind"], "typecheck")
        self.assertEqual(cands[0]["argv"], [
            os.path.join(self.repo, "node_modules/.bin/tsc"), "--noEmit", "-p",
            "pkg/web/tsconfig.json"])

    def test_tsc_without_tsconfig_is_no_typecheck(self):
        self.r("x.ts")
        self.local("node_modules/.bin/tsc")
        self.assertEqual(self.kinds("x.ts"), [])

    def test_eslint_lint(self):
        self.r("x.js")
        self.local("node_modules/.bin/eslint")
        cands = self.pick("x.js")
        self.assertEqual(cands[0]["kind"], "lint")
        self.assertEqual(cands[0]["argv"], [
            os.path.join(self.repo, "node_modules/.bin/eslint"), "x.js"])

    def test_node_check_for_js_only(self):
        self.r("x.js")
        self.r("y.ts")
        self.on_path("node")
        cands = self.pick("x.js")
        self.assertEqual(cands, [{"kind": "syntax", "argv": ["node", "--check", "x.js"],
                                  "display": "node --check x.js", "inproc": None,
                                  "target": "x.js"}])
        self.assertEqual(self.kinds("y.ts"), [])

    def test_full_ts_order(self):
        self.r("tsconfig.json", "{}")
        self.r("a.ts")
        self.r("a.test.ts")
        for b in ("vitest", "tsc", "eslint"):
            self.local("node_modules/.bin/" + b)
        self.assertEqual(self.kinds("a.ts"), ["test", "typecheck", "lint"])


class TestPickGoShellJson(TreeCase):

    def test_go_test_and_vet(self):
        self.r("pkg/x.go", "package pkg\n")
        self.r("pkg/x_test.go", "package pkg\n")
        self.on_path("go")
        cands = self.pick("pkg/x.go")
        self.assertEqual([c["argv"] for c in cands],
                         [["go", "test", "./pkg"], ["go", "vet", "./pkg"]])
        self.assertEqual([c["kind"] for c in cands], ["test", "typecheck"])

    def test_go_without_test_file(self):
        self.r("x.go", "package main\n")
        self.on_path("go")
        cands = self.pick("x.go")
        self.assertEqual([c["argv"] for c in cands], [["go", "vet", "."]])

    def test_go_absent(self):
        self.r("x.go")
        self.r("x_test.go")
        self.assertEqual(self.kinds("x.go"), [])

    def test_shell_bash_n(self):
        self.r("run.sh", "echo hi\n")
        self.on_path("bash")
        self.assertEqual(self.pick("run.sh")[0]["argv"], ["bash", "-n", "run.sh"])

    def test_json_inproc(self):
        self.r("cfg.json", "{}")
        cands = self.pick("cfg.json")
        self.assertEqual(cands[0]["kind"], "syntax")
        self.assertEqual(cands[0]["inproc"], "json")

    def test_other_extension_is_none(self):
        self.r("README.md", "# hi\n")
        self.on_path("node")
        self.on_path("pytest")
        self.assertEqual(self.pick("README.md"), [])


class TestPickSafety(TreeCase):

    def test_argv_shape_everywhere(self):
        self.r("tsconfig.json", "{}")
        self.r("a.ts")
        self.r("a.test.ts")
        self.r("b.js")
        self.r("m.py")
        self.r("test_m.py")
        self.r("ruff.toml", "")
        self.r("s.sh")
        self.r("g.go")
        self.r("g_test.go")
        for b in ("vitest", "tsc", "eslint"):
            self.local("node_modules/.bin/" + b)
        self.local(".venv/bin/pytest")
        for b in ("npx", "node", "go", "ruff", "flake8", "bash", "pytest"):
            self.on_path(b)
        cands = []
        for p in ("a.ts", "b.js", "m.py", "s.sh", "g.go"):
            cands.extend(self.pick(p))
        self.assertTrue(cands)
        self.assertNotIn("npx", " ".join(all_argv_words(cands)))
        for c in cands:
            self.assertIn(c["kind"], fixcheck.KIND_ORDER)
            if c["argv"] is None:
                self.assertIn(c["inproc"], ("ast", "json"))
                continue
            self.assertTrue(all(isinstance(w, str) for w in c["argv"]))
            head = c["argv"][0]
            if os.path.isabs(head):
                self.assertTrue(head.startswith(self.repo + os.sep))
            else:
                self.assertIn(head, fixcheck.PATH_RUNNERS)
        self.assertEqual(set(fixcheck.PATH_RUNNERS),
                         {"pytest", "go", "ruff", "flake8", "bash", "node"})

    def test_kind_order_constant(self):
        self.assertEqual(fixcheck.KIND_ORDER,
                         ("test", "typecheck", "lint", "syntax", "none"))


class TestLabels(unittest.TestCase):

    def test_exact_strings(self):
        self.assertEqual(fixcheck.LABEL_NONE,
                         "problem re-checked; no automated check available")
        self.assertEqual(fixcheck.LABEL_SYNTAX, "syntax check only")
        self.assertEqual(fixcheck.label_for("syntax", "python ast parse", False),
                         "syntax check only")
        self.assertEqual(fixcheck.label_for("none", "", False),
                         "problem re-checked; no automated check available")
        self.assertEqual(
            fixcheck.label_for("none", "", True),
            "problem re-checked; no automated check available (the existing "
            "check was already failing before the fix)")
        for kind in ("test", "typecheck", "lint"):
            self.assertEqual(fixcheck.label_for(kind, "pytest -q x.py", False),
                             "verified by `pytest -q x.py`")


class TestPickCli(TreeCase):

    def test_pick_cli_prints_json(self):
        self.r("cfg.json", "{}")
        with mock.patch("sys.stdout") as out:
            rc = fixcheck.run(["pick", "--root", self.repo, "--path", "cfg.json"])
        self.assertEqual(rc, 0)
        printed = "".join(c.args[0] for c in out.write.call_args_list)
        self.assertEqual(json.loads(printed)[0]["kind"], "syntax")

    def test_pick_cli_refuses_traversal(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(fixcheck.run(
                ["pick", "--root", self.repo, "--path", "../x.py"]), 1)

    def test_pick_cli_unknown_flag(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(fixcheck.run(
                ["pick", "--root", self.repo, "--cmd", "x"]), 2)


if __name__ == "__main__":
    unittest.main()
