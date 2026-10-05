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


# ---------------------------------------------------------------- run tests

FID = "abcd1234"
ATT_A = "a" * 32
ATT_B = "b" * 32

GREEN_MOD = "def value():\n    return 1\n"
RED_MOD = "def value():\n    return 2\n"
TEST_MOD = ("import os, sys\n"
            "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
            "import mod\n"
            "assert mod.value() == 1, 'value changed'\n")


def fresh_baseline_used(record, attempt, kind, path="mod.py"):
    """Did `baseline` build a FRESH record for `attempt` that selected `kind`?"""
    return (record.get("attempt") == attempt
            and record.get("paths", {}).get(path, {}).get("kind") == kind)


def _aggregate_without_unavailable(outcomes):
    """The pass-2 aggregation rule: failed, else timeout, else passed."""
    if not outcomes:
        return "not-run"
    if "failed" in outcomes:
        return "failed"
    if "timeout" in outcomes:
        return "timeout"
    return "passed"


class RunCase(TreeCase):

    def setUp(self):
        super().setUp()
        self.calls = os.path.join(self.root, "calls.log")
        self.finding = os.path.join(self.root, "finding.json")
        self.set_paths(["mod.py"])

    def set_paths(self, paths, fid=FID):
        write(self.finding, json.dumps({"id": fid, "paths": paths,
                                        "title": "x", "pass_number": 1}))

    def runner(self):
        return os.path.join(self.repo, ".venv/bin/pytest")

    def install_runner(self):
        fake_exe(self.runner(),
                 'echo run >> "%s"\nfor last; do :; done\nexec "%s" "$last"\n'
                 % (self.calls, sys.executable))

    def install_sleeper(self, pidfile):
        fake_exe(self.runner(),
                 '/bin/sleep 30 &\necho $! > "%s"\nwait\n' % pidfile)

    def ncalls(self):
        if not os.path.exists(self.calls):
            return 0
        with open(self.calls) as fh:
            return len(fh.read().splitlines())

    def record_path(self, fid=FID):
        return os.path.join(self.repo, ".turingmind", "fixcheck", fid + ".json")

    def record(self):
        with open(self.record_path()) as fh:
            return json.load(fh)

    def cli(self, *argv):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = fixcheck.run(list(argv))
        text = out.getvalue().strip()
        try:
            payload = json.loads(text) if text else None
        except ValueError:
            payload = text
        return rc, payload

    def baseline(self, attempt=ATT_A):
        return self.cli("baseline", "--root", self.repo, "--finding-json",
                        self.finding, "--attempt", attempt)

    def after(self, attempt=ATT_A):
        return self.cli("after", "--root", self.repo, "--finding-json",
                        self.finding, "--attempt", attempt)

    def green_tree(self):
        self.r("mod.py", GREEN_MOD)
        self.r("test_mod.py", TEST_MOD)
        self.install_runner()


class TestBaselineAfter(RunCase):

    def test_green_baseline_then_passed(self):
        self.green_tree()
        rc, summary = self.baseline()
        self.assertEqual(rc, 0)
        self.assertEqual(self.record()["paths"]["mod.py"]["kind"], "test")
        rc, res = self.after()
        self.assertEqual(rc, 0)
        self.assertEqual(res["kind"], "test")
        self.assertEqual(res["outcome"], "passed")
        self.assertEqual(res["command"],
                         ".venv/bin/pytest -q -x -p no:cacheprovider test_mod.py")
        self.assertEqual(res["label"], "verified by `.venv/bin/pytest -q -x -p "
                                       "no:cacheprovider test_mod.py`")
        self.assertEqual(res["tail"], "")
        self.assertFalse(os.path.exists(self.record_path()))

    def test_breaking_edit_fails(self):
        self.green_tree()
        self.baseline()
        self.r("mod.py", RED_MOD)
        rc, res = self.after()
        self.assertEqual(rc, 1)
        self.assertEqual(res["outcome"], "failed")
        self.assertIn("value changed", res["tail"])
        self.assertLessEqual(len(res["tail"].splitlines()), 40)

    def baseline_red_reports(self):
        """Red test at baseline -> (after result, rc). Must never be `failed`."""
        self.r("mod.py", RED_MOD)
        self.r("test_mod.py", TEST_MOD)
        self.install_runner()
        self.baseline()
        rc, res = self.after()
        return rc, res

    def test_baseline_red_downgrades_to_syntax(self):
        rc, res = self.baseline_red_reports()
        self.assertEqual(rc, 0)
        self.assertEqual(res["kind"], "syntax")
        self.assertEqual(res["outcome"], "passed")
        self.assertEqual(res["label"], "syntax check only")

    def test_only_red_candidates_is_none_already_failing(self):
        self.r("mod.py", "def value(:\n")
        self.r("test_mod.py", TEST_MOD)
        self.install_runner()
        self.baseline()
        entry = self.record()["paths"]["mod.py"]
        self.assertEqual(entry["kind"], "none")
        self.assertTrue(entry["already_failing"])
        rc, res = self.after()
        self.assertEqual(rc, 0)
        self.assertEqual(res["outcome"], "not-run")
        self.assertEqual(res["kind"], "none")
        self.assertEqual(res["label"], fixcheck.LABEL_NONE_ALREADY_FAILING)

    def test_no_runner_anywhere_is_not_red(self):
        self.r("mod.py", GREEN_MOD)
        self.r("test_mod.py", TEST_MOD)
        self.baseline()
        entry = self.record()["paths"]["mod.py"]
        self.assertEqual(entry["kind"], "syntax")
        self.assertFalse(entry["already_failing"])

    def test_none_kind_plain_label(self):
        self.set_paths(["README.md"])
        self.r("README.md", "# hi\n")
        self.baseline()
        rc, res = self.after()
        self.assertEqual(rc, 0)
        self.assertEqual(res["outcome"], "not-run")
        self.assertEqual(res["label"], fixcheck.LABEL_NONE)

    def test_syntax_error_edit_fails(self):
        self.r("mod.py", GREEN_MOD)
        self.baseline()
        self.r("mod.py", "def value(:\n")
        rc, res = self.after()
        self.assertEqual(rc, 1)
        self.assertEqual(res["kind"], "syntax")
        self.assertEqual(res["outcome"], "failed")

    def test_after_without_baseline_is_2(self):
        self.green_tree()
        rc, _ = self.after()
        self.assertEqual(rc, 2)
        self.assertEqual(self.ncalls(), 0)

    def test_baseline_twice_same_attempt_keeps_first(self):
        self.green_tree()
        self.baseline()
        self.assertEqual(self.ncalls(), 1)
        first = self.record()
        self.baseline()
        self.assertEqual(self.ncalls(), 1)
        self.assertEqual(self.record(), first)

    def test_multi_path_test_plus_none(self):
        self.green_tree()
        self.r("README.md", "# hi\n")
        self.set_paths(["mod.py", "README.md"])
        self.baseline()
        rc, res = self.after()
        self.assertEqual(rc, 0)
        self.assertEqual(res["kind"], "test")
        self.assertEqual(res["outcome"], "passed")

    def test_multi_path_one_failed(self):
        self.green_tree()
        self.r("other.py", "y = 2\n")
        self.set_paths(["mod.py", "other.py"])
        self.baseline()
        self.r("other.py", "y = (\n")
        rc, res = self.after()
        self.assertEqual(rc, 1)
        self.assertEqual(res["outcome"], "failed")
        self.assertEqual(res["kind"], "test")


class TestRunnerLost(RunCase):

    def u1_runner_deleted(self):
        self.green_tree()
        self.baseline()
        os.unlink(self.runner())
        return self.after()

    def u3_multi_path(self):
        self.green_tree()
        self.r("other.py", "y = 2\n")
        self.set_paths(["mod.py", "other.py"])
        self.baseline()
        os.unlink(self.runner())
        return self.after()

    def test_u1_runner_deleted_is_unavailable(self):
        rc, res = self.u1_runner_deleted()
        self.assertEqual(rc, 1)
        self.assertEqual(res["outcome"], "unavailable")
        self.assertIn("check could not run", res["tail"])

    def test_u2_runner_lost_exec_permission(self):
        self.green_tree()
        self.baseline()
        os.chmod(self.runner(), 0o644)
        rc, res = self.after()
        self.assertEqual(rc, 1)
        self.assertEqual(res["outcome"], "unavailable")

    def test_u3_multi_path_never_passed(self):
        rc, res = self.u3_multi_path()
        self.assertEqual(rc, 1)
        self.assertEqual(res["outcome"], "unavailable")

    def test_u4_unreadable_target(self):
        self.r("mod.py", GREEN_MOD)
        self.baseline()
        target = os.path.join(self.repo, "mod.py")
        os.chmod(target, 0)
        try:
            rc, res = self.after()
        finally:
            os.chmod(target, 0o644)
        self.assertEqual(rc, 1)
        self.assertEqual(res["outcome"], "unavailable")
        self.assertIn("file unreadable", res["tail"])

    def test_aggregate_precedence(self):
        agg = fixcheck._aggregate_outcome
        self.assertEqual(agg([]), "not-run")
        self.assertEqual(agg(["passed", "unavailable"]), "unavailable")
        self.assertEqual(agg(["unavailable", "timeout"]), "timeout")
        self.assertEqual(agg(["timeout", "failed"]), "failed")
        self.assertEqual(agg(["passed", "bogus"]), "unavailable")
        self.assertEqual(agg(["passed", "passed"]), "passed")


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class TestTimeout(RunCase):

    def timeout_case(self):
        """-> (rc, outcome, grandchild_dead)."""
        self.green_tree()
        self.baseline()
        pidfile = os.path.join(self.root, "child.pid")
        self.install_sleeper(pidfile)
        pid = None
        try:
            with mock.patch.dict(fixcheck.TIMEOUTS, {"test": 2}):
                rc, res = self.after()
            with open(pidfile) as fh:
                pid = int(fh.read().strip())
            deadline = time.time() + 3
            while _pid_alive(pid) and time.time() < deadline:
                time.sleep(0.05)
            return rc, res["outcome"], not _pid_alive(pid)
        finally:
            if pid is not None and _pid_alive(pid):
                try:
                    os.kill(pid, 9)
                except OSError:
                    pass

    def test_timeout_kills_process_group(self):
        rc, outcome, dead = self.timeout_case()
        self.assertEqual(rc, 1)
        self.assertEqual(outcome, "timeout")
        self.assertTrue(dead)


class TestAttemptScoping(RunCase):

    def stale_then_fresh(self):
        """A baselines with no runner (interrupted), runner arrives, B baselines."""
        self.r("mod.py", GREEN_MOD)
        self.r("test_mod.py", TEST_MOD)
        self.baseline(ATT_A)
        self.assertEqual(self.record()["paths"]["mod.py"]["kind"], "syntax")
        self.install_runner()
        self.baseline(ATT_B)
        return self.record()

    def test_fresh_attempt_discards_stale_record(self):
        record = self.stale_then_fresh()
        self.assertTrue(fresh_baseline_used(record, ATT_B, "test"))
        before = self.ncalls()
        rc, _ = self.after(ATT_A)
        self.assertEqual(rc, 2)
        self.assertEqual(self.ncalls(), before)
        self.assertTrue(os.path.exists(self.record_path()))
        rc, res = self.after(ATT_B)
        self.assertEqual(rc, 0)
        self.assertEqual(res["kind"], "test")
        self.assertEqual(res["outcome"], "passed")

    def stale_after_rejected(self):
        """B's record exists; `after --attempt A` -> (rc, runner ran?)."""
        self.green_tree()
        self.baseline(ATT_B)
        before = self.ncalls()
        rc, _ = self.after(ATT_A)
        return rc, self.ncalls() != before

    def test_after_with_other_attempt_runs_nothing(self):
        rc, ran = self.stale_after_rejected()
        self.assertEqual(rc, 2)
        self.assertFalse(ran)

    def test_reverse_availability(self):
        self.green_tree()
        self.baseline(ATT_A)
        self.assertEqual(self.record()["paths"]["mod.py"]["kind"], "test")
        os.unlink(self.runner())
        self.baseline(ATT_B)
        self.assertFalse(fresh_baseline_used(self.record(), ATT_B, "test"))
        self.assertEqual(self.record()["paths"]["mod.py"]["kind"], "syntax")

    def test_unreadable_record_is_discarded(self):
        self.green_tree()
        write(self.record_path(), "{not json")
        rc, _ = self.baseline(ATT_A)
        self.assertEqual(rc, 0)
        self.assertTrue(fresh_baseline_used(self.record(), ATT_A, "test"))

    def test_malformed_attempt_refused(self):
        self.green_tree()
        for bad in ("../x", "a" * 31, "A" * 32):
            rc, _ = self.baseline(bad)
            self.assertEqual(rc, 1, bad)
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".turingmind")))


class TestRefusals(RunCase):

    def test_non_hex_id(self):
        self.r("mod.py", GREEN_MOD)
        self.set_paths(["mod.py"], fid="NOTHEX!!")
        rc, _ = self.baseline()
        self.assertEqual(rc, 1)

    def test_traversal_path(self):
        self.set_paths(["../x.py"])
        rc, _ = self.baseline()
        self.assertEqual(rc, 1)

    def test_unknown_flag(self):
        rc, _ = self.cli("baseline", "--root", self.repo, "--finding-json",
                         self.finding, "--attempt", ATT_A, "--cmd", "x")
        self.assertEqual(rc, 2)

    def test_missing_attempt(self):
        rc, _ = self.cli("after", "--root", self.repo, "--finding-json",
                         self.finding)
        self.assertEqual(rc, 2)

    def test_nothing_written_on_refusal(self):
        self.set_paths(["../x.py"])
        self.baseline()
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".turingmind")))


class TestFixcheckMutants(RunCase):
    """Every lock must trip: each mutant flips a named case."""

    def test_a_baseline_accepting_red(self):
        rc, res = TestBaselineAfter.baseline_red_reports(self)
        self.assertNotEqual(res["outcome"], "failed")
        self.setUp_again()
        mutant = lambda outcome: outcome in ("passed", "failed")  # noqa: E731
        self.assertNotEqual(mutant("failed"), fixcheck._usable_at_baseline("failed"))
        with mock.patch.object(fixcheck, "_usable_at_baseline", mutant):
            rc, res = TestBaselineAfter.baseline_red_reports(self)
        self.assertEqual(res["outcome"], "failed")

    def test_b_direct_child_only_kill(self):
        rc, outcome, dead = TestTimeout.timeout_case(self)
        self.assertTrue(dead)
        self.setUp_again()
        real_kill = os.kill
        with mock.patch.object(fixcheck.os, "killpg",
                               lambda pgid, sig: real_kill(pgid, sig)):
            self.assertIsNot(fixcheck.os.killpg, os.kill)
            rc, outcome, dead = TestTimeout.timeout_case(self)
        self.assertEqual(outcome, "timeout")
        self.assertFalse(dead)

    def test_c_syntax_label_swapped(self):
        self.assertEqual(fixcheck.label_for("syntax", "", False), "syntax check only")
        with mock.patch.object(fixcheck, "LABEL_SYNTAX", fixcheck.LABEL_NONE):
            self.assertNotEqual(fixcheck.label_for("syntax", "", False),
                                "syntax check only")
            rc, res = TestBaselineAfter.baseline_red_reports(self)
        self.assertNotEqual(res["label"], "syntax check only")

    def test_d_stale_record_reused(self):
        record = TestAttemptScoping.stale_then_fresh(self)
        self.assertTrue(fresh_baseline_used(record, ATT_B, "test"))
        self.setUp_again()
        with mock.patch.object(fixcheck, "_record_matches_attempt",
                               lambda record, attempt: True):
            self.assertTrue(fixcheck._record_matches_attempt({}, ATT_A))
            record = TestAttemptScoping.stale_then_fresh(self)
        self.assertFalse(fresh_baseline_used(record, ATT_B, "test"))

    def test_e_after_accepts_other_attempt(self):
        rc, ran = TestAttemptScoping.stale_after_rejected(self)
        self.assertEqual((rc, ran), (2, False))
        self.setUp_again()
        with mock.patch.object(fixcheck, "_record_matches_attempt",
                               lambda record, attempt: True):
            rc, ran = TestAttemptScoping.stale_after_rejected(self)
        self.assertNotEqual(rc, 2)
        self.assertTrue(ran)

    def test_f_aggregate_without_unavailable(self):
        rc, res = TestRunnerLost.u3_multi_path(self)
        self.assertEqual((rc, res["outcome"]), (1, "unavailable"))
        self.setUp_again()
        probe = ["passed", "unavailable"]
        self.assertNotEqual(_aggregate_without_unavailable(probe),
                            fixcheck._aggregate_outcome(probe))
        with mock.patch.object(fixcheck, "_aggregate_outcome",
                               _aggregate_without_unavailable):
            rc, res = TestRunnerLost.u3_multi_path(self)
        self.assertEqual((rc, res["outcome"]), (0, "passed"))

    def test_g_could_not_run_maps_to_passed(self):
        rc, res = TestRunnerLost.u1_runner_deleted(self)
        self.assertEqual(rc, 1)
        self.setUp_again()
        real = fixcheck.run_check

        def mutant(root, check, timeout):
            result = real(root, check, timeout)
            if result["outcome"] == "unavailable":
                return {"outcome": "passed", "tail": ""}
            return result

        with mock.patch.object(fixcheck, "run_check", mutant):
            self.assertIsNot(fixcheck.run_check, real)
            rc, res = TestRunnerLost.u1_runner_deleted(self)
        self.assertEqual(rc, 0)
        self.assertEqual(res["outcome"], "passed")

    def setUp_again(self):
        """Fresh fixture tree for the mutant half of a case."""
        self._env.stop()
        self._tmp.cleanup()
        RunCase.setUp(self)


if __name__ == "__main__":
    unittest.main()
