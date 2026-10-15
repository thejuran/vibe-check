"""Tests for holdout_eval_launch — the holdout measurement launcher.

Synthetic fixtures only: the case folder is a temp dir named by a fresh
opaque id (made unreadable, so any read, listing or hash under it would
fail), the build repo is the freeze kit's own temp-repo fixture, and the
identity check and the session are mocked. No real manifest, home, holdout
folder or session is ever touched.

Every lock is paired with a mutant that patches the guard out and shows the
wrong outcome happens.
"""

import argparse
import ast
import contextlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)
FREEZE_TOOLS = os.path.join(os.path.dirname(os.path.dirname(TOOLS_DIR)),
                            "freeze-v2.12", "tools")
sys.path.insert(0, FREEZE_TOOLS)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_autopilot  # noqa: E402
import holdout_eval_launch as el  # noqa: E402
import freeze_manifest as fm  # noqa: E402
import freeze_policy  # noqa: E402
from test_freeze_check import VALIDATION_COMMANDS  # noqa: E402
from test_freeze_manifest import _Fixture  # noqa: E402

LAUNCHER_PY = os.path.join(TOOLS_DIR, "holdout_eval_launch.py")
KitError = holdout_kit.KitError


def _calls(tree, func_name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return node
    return None


def _call_name(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _first_line(fn, name):
    lines = [n.lineno for n in ast.walk(fn)
             if isinstance(n, ast.Call) and _call_name(n) == name]
    return min(lines) if lines else None


def check_precedes_spawn_holds(source):
    """launch() calls verify, then write_identity, then spawn — in that
    order, each present."""
    fn = _calls(ast.parse(source), "launch")
    if fn is None:
        return False
    v, w, s = (_first_line(fn, n) for n in ("verify", "write_identity",
                                             "spawn"))
    return None not in (v, w, s) and v < w < s


def settings_bound_holds(source):
    """The settings path the check sees is the one the session gets: the
    verify call's settings_path= and build_argv's settings_path= are the same
    local name, `settings_path`."""
    fn = _calls(ast.parse(source), "launch")
    if fn is None:
        return False
    seen = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and _call_name(node) in ("verify",
                                                              "build_argv"):
            for kw in node.keywords:
                if kw.arg == "settings_path":
                    seen.setdefault(_call_name(node), []).append(
                        kw.value.id if isinstance(kw.value, ast.Name)
                        else None)
    return seen.get("verify") == ["settings_path"] \
        and seen.get("build_argv") == ["settings_path"]


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


class _Result:
    def __init__(self, problems, candidate):
        self.problems = problems
        self.manifest_id = "a" * 64
        self.check_digest = "b" * 64
        self.candidate_sha = candidate


class LaunchCase(unittest.TestCase):
    """A temp build repo (the freeze kit's _Fixture), a synthetic unreadable
    case folder, a mocked check and a recording spawn."""

    @classmethod
    def setUpClass(cls):
        cls.fx = _Fixture()
        cls.candidate = subprocess.run(
            ["git", "-C", cls.fx.repo, "rev-parse", "HEAD"],
            stdout=subprocess.PIPE, check=True, timeout=60
        ).stdout.decode().strip()

    @classmethod
    def tearDownClass(cls):
        cls.fx.close()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = os.path.realpath(self._tmp.name)
        self.case_id = holdout_fixture._new_id(set())
        self.case = os.path.join(self.base, "cases", self.case_id)
        holdout_fixture.write(self.case, "SENTINEL.txt", "sealed-sentinel\n")
        os.chmod(self.case, 0)
        self.addCleanup(os.chmod, self.case, stat.S_IRWXU)
        self.run_dir = os.path.join(self.base, "runs", self.case_id, "run-1")
        self.manifest = {
            "manifest_id": "a" * 64, "candidate_sha": self.candidate,
            "runners": {"holdout-eval": {"launch_model": {
                "value": "claude-fixture-1[1m]"}}}}
        self.problems = []
        self.verify_calls = []
        self.spawned = []
        self.events = []
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.load = stack.enter_context(mock.patch.object(
            el.freeze_check, "load_manifest",
            side_effect=lambda path: self.manifest))
        self.active = stack.enter_context(mock.patch.object(
            el.freeze_check, "active_manifest",
            side_effect=lambda repo: os.path.join(repo, "M.json")))

    def verify(self, manifest, runner, **kw):
        self.events.append("verify")
        self.verify_calls.append((manifest, runner, kw))
        return _Result(list(self.problems), manifest["candidate_sha"])

    def spawn(self, argv, env, cwd):
        self.events.append("spawn")
        self.spawned.append({
            "argv": argv, "env": env, "cwd": cwd,
            "identity_present": os.path.isfile(
                os.path.join(self.run_dir, "identity.json"))})

    def launch(self, run_dir=None, case=None, **kw):
        out = io.StringIO()
        kw.setdefault("repo", self.fx.repo)
        kw.setdefault("verify", self.verify)
        kw.setdefault("spawn", self.spawn)
        kw.setdefault("home", self.fx.home)
        kw.setdefault("env", {"PATH": "/usr/bin:/bin",
                              "ANTHROPIC_API_KEY": "planted-key"})
        rc = el.launch(run_dir or self.run_dir, case or self.case, out=out,
                       **kw)
        return rc, out.getvalue()


class TestLaunch(LaunchCase):

    def test_check_precedes_spawn(self):
        rc, out = self.launch()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.events, ["verify", "spawn"])
        manifest, runner, kw = self.verify_calls[0]
        self.assertEqual(runner, "holdout-eval")
        self.assertEqual(kw["clone_dir"], self.run_dir)
        self.assertEqual(kw["launch_model"], "claude-fixture-1[1m]")
        self.assertEqual(kw["home"], self.fx.home)
        self.assertEqual(kw["repo"], os.path.realpath(self.fx.repo))
        self.assertEqual(kw["plugin_dir"], os.path.join(
            self.run_dir, "frozen-build", "plugins", "vibe-check"))
        self.assertIn("IDENTITY OK manifest_id=" + "a" * 64, out)

    def test_mismatch_stops_before_spawn(self):
        self.problems = ["file differs: agents/a.md (manifest 111111111111 "
                         "live 222222222222)",
                         "setting differs: launch_model (manifest x live y)"]
        rc, out = self.launch()
        self.assertEqual(rc, 1)
        self.assertEqual(self.spawned, [])
        for line in self.problems:
            self.assertIn(line, out)
        self.assertTrue(out.rstrip().endswith("IDENTITY MISMATCH — STOPPING"))
        self.assertFalse(os.path.exists(os.path.join(self.run_dir,
                                                     "identity.json")))

    def test_check_error_fails_closed(self):
        def boom(*a, **kw):
            raise RuntimeError("collector broke")
        rc, out = self.launch(verify=boom)
        self.assertEqual(rc, 1)
        self.assertEqual(self.spawned, [])
        self.assertIn("IDENTITY MISMATCH — STOPPING", out)

    def test_no_manifest_stops(self):
        self.active.side_effect = el.freeze_common.FreezeError("none")
        rc, out = self.launch()
        self.assertEqual(rc, 1)
        self.assertIn("no active freeze manifest — STOPPING", out)
        self.assertEqual(self.events, [])

    def test_identity_json_written_before_spawn(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        self.assertTrue(self.spawned[0]["identity_present"])
        with open(os.path.join(self.run_dir, "identity.json")) as fh:
            rec = json.load(fh)
        self.assertEqual(rec["manifest_id"], "a" * 64)
        self.assertEqual(rec["check_digest"], "b" * 64)
        self.assertEqual(rec["candidate_sha"], self.candidate)
        self.assertEqual(rec["runner"], "holdout-eval")
        self.assertEqual(rec["session_id"],
                         self.spawned[0]["argv"][
                             self.spawned[0]["argv"].index("--session-id") + 1])

    def test_identity_json_case_and_run(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        with open(os.path.join(self.run_dir, "identity.json")) as fh:
            rec = json.load(fh)
        self.assertEqual(rec["case_id"], self.case_id)
        self.assertEqual(rec["run_name"], "run-1")
        # The shape freeze_policy.read_record reads: kind holdout-eval with a
        # (case, repetition) slot and all three stamps.
        got = freeze_policy.read_record(self.run_dir)
        self.assertEqual(got["kind"], "holdout-eval")
        self.assertEqual(got["slot"], (self.case_id, 1))
        self.assertTrue(got["identity_ok"], got["identity_reason"])
        # A case path that is not named by an H- id, and a run dir not named
        # run-<n>, each stop before anything runs.
        bad_case = os.path.join(self.base, "cases", "alpha-case")
        rc, out = self.launch(case=bad_case)
        self.assertEqual(rc, 1)
        self.assertIn("H-<8 hex>", out)
        bad_run = os.path.join(self.base, "runs", self.case_id, "attempt-2")
        rc, out = self.launch(run_dir=bad_run)
        self.assertEqual(rc, 1)
        self.assertIn("run-<n>", out)
        self.assertEqual(len(self.spawned), 1)
        self.assertEqual(len(self.verify_calls), 1)
        self.assertFalse(os.path.exists(bad_run))

    def test_identity_json_never_overwritten(self):
        self.assertEqual(self.launch()[0], 0)
        rc, out = self.launch()
        self.assertEqual(rc, 1)
        self.assertIn("NEW run dir", out)
        self.assertEqual(len(self.spawned), 1)

    def test_retry_rechecks(self):
        self.assertEqual(self.launch()[0], 0)
        run2 = os.path.join(os.path.dirname(self.run_dir), "run-2")
        self.assertEqual(self.launch(run_dir=run2)[0], 0)
        self.assertEqual(self.events, ["verify", "spawn", "verify", "spawn"])
        self.assertEqual(freeze_policy.read_record(run2)["slot"],
                         (self.case_id, 2))

    def test_case_folder_is_opaque(self):
        # The case folder is unreadable (mode 000) and the launch still works:
        # nothing under it was read, listed or hashed. It reaches the session
        # only as the --add-dir value.
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        argv = self.spawned[0]["argv"]
        self.assertEqual(argv[argv.index("--add-dir") + 1], self.case)
        self.assertEqual(argv.count(self.case), 1)
        for _m, _r, kw in self.verify_calls:
            self.assertNotIn(self.case, json.dumps(kw, default=str))

    def test_untracked_not_materialized(self):
        stray = os.path.join(self.fx.repo, "plugins", "vibe-check", "agents",
                             "untracked-stray.md")
        edited = os.path.join(self.fx.repo, "plugins", "vibe-check", "agents",
                              "a.md")
        with open(edited) as fh:
            original = fh.read()
        try:
            holdout_fixture.write(self.fx.repo,
                                  "plugins/vibe-check/agents/untracked-stray.md",
                                  "stray\n")
            with open(edited, "w") as fh:
                fh.write("uncommitted edit\n")
            dest = os.path.join(self.base, "build")
            plugin = el.materialize_plugin_from_candidate(
                self.fx.repo, self.candidate, dest)
        finally:
            os.remove(stray)
            with open(edited, "w") as fh:
                fh.write(original)
        self.assertFalse(os.path.exists(os.path.join(plugin, "agents",
                                                     "untracked-stray.md")))
        with open(os.path.join(plugin, "agents", "a.md")) as fh:
            self.assertEqual(fh.read(), original)
        self.assertTrue(os.access(os.path.join(dest, "statusline-capture.sh"),
                                  os.X_OK))

    def test_materialize_refuses_existing_dest(self):
        dest = os.path.join(self.base, "build")
        os.makedirs(dest)
        with self.assertRaises(KitError):
            el.materialize_plugin_from_candidate(self.fx.repo, self.candidate,
                                                 dest)

    def test_other_candidate_is_a_problem(self):
        parent = subprocess.run(
            ["git", "-C", self.fx.repo, "rev-parse", "HEAD~1"],
            stdout=subprocess.PIPE, check=True, timeout=60
        ).stdout.decode().strip()
        # HEAD~1 has no runner settings yet, so build a candidate-sized
        # mismatch by naming HEAD under the manifest of another candidate.
        self.manifest["candidate_sha"] = parent
        rc, out = self.launch(candidate=self.candidate)
        self.assertEqual(rc, 1)
        self.assertIn("is not the manifest candidate", out)
        self.assertEqual(self.spawned, [])

    def test_settings_path_same_for_verify_and_spawn(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        settings = self.verify_calls[0][2]["settings_path"]
        argv = self.spawned[0]["argv"]
        self.assertEqual(argv[argv.index("--settings") + 1], settings)
        build = os.path.join(self.run_dir, "frozen-build")
        self.assertEqual(settings, os.path.join(build,
                                                "settings-measured.json"))
        with open(settings) as fh:
            got = json.load(fh)
        want = json.loads(json.dumps(self.fx.template).replace("<RUNNER>",
                                                               build))
        self.assertEqual(got, want)
        self.assertEqual(got["statusLine"]["command"],
                         build + "/statusline-capture.sh")
        self.assertEqual(argv[argv.index("--plugin-dir") + 1],
                         self.verify_calls[0][2]["plugin_dir"])
        self.assertEqual(argv[argv.index("--model") + 1],
                         self.verify_calls[0][2]["launch_model"])

    def test_env_checked_is_env_launched(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        checked = self.verify_calls[0][2]["env"]
        self.assertIs(checked, self.spawned[0]["env"])
        self.assertNotIn("ANTHROPIC_API_KEY", checked)
        self.assertEqual(checked["DISABLE_AUTOUPDATER"], "1")
        self.assertEqual(checked["DISABLE_UPDATES"], "1")
        self.assertEqual(self.spawned[0]["cwd"], self.run_dir)

    def test_argv_passes_autopilot_rules(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        argv = self.spawned[0]["argv"]
        holdout_autopilot.check_argv(argv)
        self.assertEqual(argv[0], "claude")
        for bad in el.FORBIDDEN_ARGS:
            if bad != "--permission-mode":
                self.assertNotIn(bad, argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")


class TestShape(unittest.TestCase):

    def setUp(self):
        with open(LAUNCHER_PY, encoding="utf-8") as fh:
            self.text = fh.read()
        self.tree = ast.parse(self.text)

    def test_no_override_flags(self):
        parser = el.build_parser()
        sub = next(a for a in parser._actions
                   if isinstance(a, argparse._SubParsersAction))
        opts = set()
        for p in [parser] + list(sub.choices.values()):
            for action in p._actions:
                opts.update(action.option_strings)
        self.assertIn("--run-dir", opts)
        for opt in opts:
            self.assertIsNone(
                re.search(r"force|skip|override|allow|ignore|home|bypass",
                          opt), opt)

    def test_no_home_in_production_shape(self):
        # The check's argv for this runner is exactly the 54-05 production
        # shape: no --home / --codex-home, so the real home is checked.
        self.assertEqual(VALIDATION_COMMANDS["holdout-eval"][:4],
                         ["verify", "--runner", "holdout-eval", "--plugin-dir"])
        self.assertNotIn("--home", VALIDATION_COMMANDS["holdout-eval"])
        fn = _calls(self.tree, "cmd")
        kws = {kw.arg for n in ast.walk(fn) if isinstance(n, ast.Call)
               for kw in n.keywords}
        self.assertNotIn("home", kws)

    def test_forbidden_text_absent(self):
        for bad in ("vibe-check-holdout", "--bare",
                    "--dangerously-skip-permissions",
                    "--no-session-persistence", "bypassPermissions",
                    "holdout_fixture", "subprocess", "dangerously"):
            self.assertNotIn(bad, self.text, bad)

    def test_import_set(self):
        self.assertEqual(_imports(self.tree),
                         {"argparse", "json", "os", "re", "sys", "time",
                          "holdout_kit", "holdout_autopilot", "freeze_check",
                          "freeze_common"})

    def test_reused_constants(self):
        self.assertIs(el.FORBIDDEN_ARGS, holdout_autopilot.FORBIDDEN_ARGS)
        self.assertIs(el.STRIPPED_ENV, holdout_autopilot.STRIPPED_ENV)
        self.assertEqual(el.RUNNER_TEMPLATE, fm.RUNNER_TEMPLATE)
        self.assertEqual(el.RUNNER_STATUSLINE, fm.RUNNER_STATUSLINE)
        self.assertEqual(el.RUNNER_PLACEHOLDER,
                         fm.RUNNER_SUBSTITUTION["placeholder"])

    def test_locks_hold_on_source(self):
        self.assertTrue(check_precedes_spawn_holds(self.text))
        self.assertTrue(settings_bound_holds(self.text))

    def test_cli_usage_exit_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(el.main(["bogus"]), 2)
            self.assertEqual(el.main([]), 2)
            self.assertEqual(el.main(["eval-launch", "--case", "x"]), 2)

    def test_cli_refuses_in_claude_shell(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}), \
                mock.patch.object(el, "launch") as launch, \
                contextlib.redirect_stderr(io.StringIO()) as err:
            rc = el.main(["eval-launch", "--run-dir", "/tmp/x/run-1",
                          "--case", "/tmp/x/H-00000000"])
        self.assertEqual(rc, 1)
        launch.assert_not_called()
        self.assertIn("eval-launch:", err.getvalue())

    def test_kit_dispatch(self):
        self.assertEqual(holdout_kit.COMMANDS["eval-launch"],
                         "holdout_eval_launch")
        self.assertNotIn("eval-launch", holdout_kit.NO_REFUSAL_COMMANDS)


class TestMutants(LaunchCase):

    def test_mutant_a_problems_mean_no_spawn(self):
        self.assertEqual(self.launch()[0], 0)
        self.assertEqual(len(self.spawned), 1)
        run2 = os.path.join(os.path.dirname(self.run_dir), "run-2")
        with mock.patch.object(self, "problems", ["file extra: agents/z.md"]):
            rc, _ = self.launch(run_dir=run2)
        self.assertEqual(rc, 1)
        self.assertEqual(len(self.spawned), 1)

    def test_mutant_b_verify_removed_fails_lock(self):
        with open(LAUNCHER_PY, encoding="utf-8") as fh:
            text = fh.read()
        old = "            result = verify(manifest, RUNNER,"
        self.assertEqual(text.count(old), 1)
        mutant = text.replace(old, "            result = _skip(manifest, RUNNER,")
        self.assertFalse(check_precedes_spawn_holds(mutant))

    def test_mutant_c_write_identity_noop_flips(self):
        self.assertEqual(self.launch()[0], 0)
        self.assertTrue(self.spawned[-1]["identity_present"])
        run2 = os.path.join(os.path.dirname(self.run_dir), "run-2")
        self.run_dir = run2
        with mock.patch.object(el, "write_identity",
                               lambda *a, **kw: None):
            self.assertEqual(self.launch(run_dir=run2)[0], 0)
        self.assertFalse(self.spawned[-1]["identity_present"])

    def test_mutant_d_other_settings_in_argv_fails_lock(self):
        with open(LAUNCHER_PY, encoding="utf-8") as fh:
            text = fh.read()
        old = "build_argv(plugin_dir=plugin_dir, settings_path=settings_path,"
        self.assertEqual(text.count(old), 1)
        mutant = text.replace(old, "build_argv(plugin_dir=plugin_dir, "
                                   "settings_path=other_settings,")
        self.assertFalse(settings_bound_holds(mutant))

    def test_mutant_e_spawn_before_check_fails_lock(self):
        with open(LAUNCHER_PY, encoding="utf-8") as fh:
            text = fh.read()
        old = "        session_env = session_environment(env)\n"
        self.assertEqual(text.count(old), 1)
        mutant = text.replace(old, old + "        spawn([], {}, run_dir)\n")
        self.assertFalse(check_precedes_spawn_holds(mutant))


if __name__ == "__main__":
    unittest.main()
