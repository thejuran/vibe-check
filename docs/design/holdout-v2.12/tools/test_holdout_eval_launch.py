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
        # A stand-in session binary on the session PATH (never executed: the
        # spawn is recorded, not run).
        self.bin = os.path.join(self.base, "bin")
        os.makedirs(self.bin)
        self.claude = os.path.join(self.bin, "claude")
        with open(self.claude, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(self.claude, 0o755)
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

    def spawn(self, argv, env, cwd, binary):
        self.events.append("spawn")
        self.spawned.append({
            "argv": argv, "env": env, "cwd": cwd, "binary": binary,
            "identity_present": os.path.isfile(
                os.path.join(self.run_dir, "identity.json"))})

    def launch(self, run_dir=None, case=None, **kw):
        out = io.StringIO()
        kw.setdefault("repo", self.fx.repo)
        kw.setdefault("verify", self.verify)
        kw.setdefault("spawn", self.spawn)
        kw.setdefault("home", self.fx.home)
        kw.setdefault("env", {"PATH": self.bin + ":/usr/bin:/bin",
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
        # The update pins live in the materialized runner settings (`env`),
        # never in the checked process env: the manifest's process-env
        # baseline comes from the generating shell, where they are unset.
        self.assertNotIn("DISABLE_AUTOUPDATER", checked)
        self.assertNotIn("DISABLE_UPDATES", checked)
        self.assertEqual(self.spawned[0]["cwd"], self.run_dir)

    def test_session_env_is_an_allowlist(self):
        """Only the identity-checked names plus what the session needs reach
        it; every other variable of the launching shell is dropped."""
        env = {"PATH": self.bin + ":/usr/bin:/bin", "HOME": "/h",
               "AWS_SECRET_ACCESS_KEY": "planted", "GITHUB_TOKEN": "planted",
               "SSH_AUTH_SOCK": "/tmp/agent.sock", "ANTHROPIC_API_KEY": "planted",
               "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5[1m]",
               "VC_CONTAINMENT_ENV_CANARY": "planted"}
        rc, _ = self.launch(env=env)
        self.assertEqual(rc, 0)
        got = self.spawned[0]["env"]
        self.assertEqual(set(got), {"PATH", "HOME", "ANTHROPIC_DEFAULT_OPUS_MODEL"})
        self.assertTrue(set(got) <= set(fm.SESSION_ENV_NAMES))

    def test_mutant_denylist_env_lets_shell_secrets_through(self):
        env = {"PATH": self.bin + ":/usr/bin:/bin", "AWS_SECRET_ACCESS_KEY": "planted"}

        def denylist(e=None):
            out = dict(e)
            for name in el.STRIPPED_ENV:
                out.pop(name, None)
            return out
        with mock.patch.object(el, "session_environment", denylist):
            rc, _ = self.launch(env=env)
        self.assertEqual(rc, 0)
        self.assertIn("AWS_SECRET_ACCESS_KEY", self.spawned[0]["env"])

    def test_argv_passes_the_launch_rules(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        argv = self.spawned[0]["argv"]
        el.check_launch_argv(argv)
        holdout_autopilot.check_argv(argv, mode="manual")
        self.assertEqual(argv[0], "claude")
        for bad in el.FORBIDDEN_ARGS:
            if bad != "--permission-mode":
                self.assertNotIn(bad, argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "manual")
        self.assertEqual(argv[argv.index("--allowedTools") + 1],
                         "Bash,Read,Write,Edit,Grep,Glob,Task,Agent")
        self.assertNotIn("dontAsk", argv)


class TestLaunchFailure(LaunchCase):
    """No eligibility record ever exists for a run that never launched."""

    def test_unresolvable_binary_stops_before_the_stamp(self):
        rc, out = self.launch(env={"PATH": "/nonexistent-bin"})
        self.assertEqual(rc, 1)
        self.assertIn(el.NO_BINARY_MSG, out)
        self.assertEqual(self.spawned, [])
        self.assertFalse(os.path.exists(os.path.join(self.run_dir,
                                                     "identity.json")))

    def test_spawn_gets_the_resolved_binary(self):
        rc, _ = self.launch()
        self.assertEqual(rc, 0)
        self.assertEqual(self.spawned[0]["binary"], self.claude)
        self.assertEqual(self.spawned[0]["argv"][0], "claude")

    def test_exec_failure_leaves_no_eligible_record(self):
        def failing(argv, env, cwd, binary):
            self.events.append("spawn")
            raise OSError(2, "No such file or directory")
        rc, out = self.launch(spawn=failing)
        self.assertEqual(rc, 1)
        self.assertIn("the session did not start", out)
        self.assertFalse(os.path.exists(os.path.join(self.run_dir,
                                                     "identity.json")))
        with open(os.path.join(self.run_dir, el.LAUNCH_FAILED_NAME),
                  encoding="utf-8") as fh:
            failed = json.load(fh)
        self.assertEqual(failed["launch_error"], "FileNotFoundError")
        rec = freeze_policy.read_record(self.run_dir)
        ok, reason = freeze_policy.eligible(
            rec, {"manifest_id": "a" * 64, "candidate_sha": self.candidate},
            freeze_policy.Prerequisites(problems=[]))
        self.assertFalse(ok, reason)

    def test_mutant_failure_mark_removed_leaves_a_stamp(self):
        def failing(argv, env, cwd, binary):
            raise OSError(2, "No such file or directory")
        with mock.patch.object(el, "_mark_launch_failed",
                               lambda run_dir, exc: None):
            rc, _ = self.launch(spawn=failing)
        self.assertEqual(rc, 1)
        self.assertTrue(os.path.exists(os.path.join(self.run_dir,
                                                    "identity.json")))

    def test_mutant_no_resolution_stamps_an_unlaunchable_run(self):
        with mock.patch.object(el, "resolve_session_binary",
                               lambda env: "claude"):
            rc, _ = self.launch(env={"PATH": "/nonexistent-bin"})
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(os.path.join(self.run_dir,
                                                    "identity.json")))


class TestRealProcessEnvCheck(unittest.TestCase):
    """The environment the launcher builds goes through the REAL identity
    check (freeze_check.verify, runner holdout-eval) on the freeze kit's
    fixture: a manifest generated from a shell without the update pins."""

    def setUp(self):
        from test_freeze_check import _CheckFixture
        self.fx = _CheckFixture()
        self.addCleanup(self.fx.close)

    def session_env(self):
        return el.session_environment({"PATH": "/usr/bin:/bin",
                                       "HOME": self.fx.home})

    def test_launcher_env_passes_the_real_check(self):
        result = self.fx.check("holdout-eval", env=self.session_env())
        self.assertEqual(result.problems, [])

    def test_update_pins_are_in_the_runner_settings(self):
        with open(self.fx.settings_path, encoding="utf-8") as fh:
            settings = json.load(fh)
        self.assertEqual(settings["env"]["DISABLE_AUTOUPDATER"], "1")
        self.assertEqual(settings["env"]["DISABLE_UPDATES"], "1")

    def test_mutant_pins_back_in_the_process_env_stop_the_launch(self):
        env = dict(self.session_env(), DISABLE_AUTOUPDATER="1",
                   DISABLE_UPDATES="1")
        problems = self.fx.check("holdout-eval", env=env).problems
        self.assertIn("setting differs: env.DISABLE_UPDATES (manifest null "
                      "live 1) [process env]", problems)


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
                          "freeze_common", "freeze_manifest"})

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


# --------------------------------------------------------------------------- #
# Manual-mode pre-approval: holdout-eval runs the session like B3
# --------------------------------------------------------------------------- #

REAL_REPO = os.path.normpath(os.path.join(TOOLS_DIR, "..", "..", "..", ".."))
REAL_TEMPLATE = os.path.join(REAL_REPO, el.RUNNER_TEMPLATE)
B3_RUNBOOK = os.path.join(REAL_REPO, "docs", "design", "reachability-dev",
                          "RUN-PHASE54-live.md")
REVIEW_COMMANDS = tuple(os.path.join(REAL_REPO, "plugins", "vibe-check",
                                     "commands", n)
                        for n in ("deep-review.md", "review.md"))
# Task's current name; the subagent dispatch is pre-approved under both.
ALIASES = {"Agent"}
# Tools the review flow uses that raise no permission prompt in manual mode
# (the fix-loop card): never pre-approved, so one list serves the settings,
# the B3 launch line and the holdout launch line.
PROMPTLESS = {"AskUserQuestion"}
# In-process network tools: never pre-approved, always denied.
NEVER_ALLOWED = ("WebFetch", "WebSearch")
# The B3 measured-session blocks whose process becomes `claude`.
B3_SESSION_BLOCKS = ("session", "proof-session")


def allowed_tool_names(command_text):
    """Base tool names a command's `allowed-tools` frontmatter names
    (`Bash(git:*)` -> `Bash`)."""
    m = re.search(r"(?m)^allowed-tools:\s*(.+)$", command_text)
    if not m:
        return set()
    return {re.sub(r"\(.*\)$", "", t.strip()) for t in m.group(1).split(",")
            if t.strip()}


def preapproval_gaps(settings, command_texts):
    """Every problem with the measured settings for a `--permission-mode
    manual` session: a prompting tool the review commands use that is not
    pre-approved (it would put a permission prompt in front of the owner), a
    pre-approval broader than the commands need (the promptless card tool
    included), or an in-process network tool not denied."""
    perms = settings.get("permissions") or {}
    allow = perms.get("allow") or []
    deny = perms.get("deny") or []
    needed = set()
    for text in command_texts:
        needed |= allowed_tool_names(text)
    needed -= PROMPTLESS
    out = ["not pre-approved: %s" % t for t in sorted(needed - set(allow))]
    out += ["pre-approved beyond the review commands: %s" % t
            for t in allow if t not in needed | ALIASES]
    out += ["%s not denied" % t for t in NEVER_ALLOWED if t not in deny]
    out += ["%s pre-approved" % t for t in NEVER_ALLOWED if t in allow]
    return out


def _flag_values(argv, flag):
    return [argv[i + 1] if i + 1 < len(argv) else None
            for i, a in enumerate(argv) if a == flag]


def b3_launch_lines(runbook_text):
    """[(block, mode, allowedTools)] of every claude launch line in B3's
    measured-session blocks."""
    out = []
    for name in B3_SESSION_BLOCKS:
        m = re.search(r"(?ms)^# BLOCK: %s\n(.*?)^# END: %s$"
                      % (re.escape(name), re.escape(name)), runbook_text)
        for ln in (m.group(1).splitlines() if m else ()):
            if ln.lstrip().startswith("#") or " claude " not in ln:
                continue
            modes = re.findall(r"--permission-mode\s+(\S+)", ln)
            tools = re.findall(r'--allowedTools\s+"([^"]*)"', ln)
            out.append((name, modes[0] if len(modes) == 1 else None,
                        tools[0] if len(tools) == 1 else None))
    return out


def same_mode_as_b3_problems(launch_argv, runbook_text, settings):
    """The holdout launcher runs the session in the permission mode and with
    the pre-approved tool list B3 uses, and that list is the measured
    settings' allow list. dontAsk is refused outright: it refuses the
    fix-loop card whatever the allow rules say."""
    argv = list(launch_argv)
    modes = _flag_values(argv, "--permission-mode")
    tools = _flag_values(argv, "--allowedTools")
    out = []
    if "dontAsk" in argv:
        out.append("holdout launcher uses dontAsk")
    mode = modes[0] if len(modes) == 1 else None
    listed = tools[0] if len(tools) == 1 else None
    b3 = b3_launch_lines(runbook_text)
    if len(b3) != len(B3_SESSION_BLOCKS):
        out.append("B3 runbook session launch lines not found")
    for name, b3_mode, b3_tools in b3:
        if mode != b3_mode:
            out.append("mode %s differs from B3 %s (%s)" % (mode, b3_mode, name))
        if listed != b3_tools:
            out.append("tools %s differ from B3 %s (%s)" % (listed, b3_tools, name))
    allow = ",".join((settings.get("permissions") or {}).get("allow") or [])
    if listed != allow:
        out.append("tools %s are not the settings allow list %s" % (listed, allow))
    return out


class TestManualModePreApproval(unittest.TestCase):
    """The launcher runs the session in manual mode, like B3: tools outside
    the pre-approved list would raise a permission prompt, so the measured
    settings pre-approve every prompting tool the review flow uses and
    nothing broader. The card tool needs no approval and is not listed."""

    def setUp(self):
        with open(REAL_TEMPLATE, encoding="utf-8") as fh:
            self.settings = json.load(fh)
        self.commands = []
        for path in REVIEW_COMMANDS:
            with open(path, encoding="utf-8") as fh:
                self.commands.append(fh.read())

    def test_commands_name_the_card_tool(self):
        for text in self.commands:
            self.assertIn("AskUserQuestion", allowed_tool_names(text))

    def test_real_template_pre_approves_the_review_tools(self):
        self.assertEqual(preapproval_gaps(self.settings, self.commands), [])
        self.assertNotIn("AskUserQuestion", self.settings["permissions"]["allow"])

    def test_launcher_reads_this_template(self):
        self.assertEqual(el.RUNNER_TEMPLATE,
                         "docs/design/b3-ground-truth/b3-runner-v2.12/"
                         "settings-measured.json")
        self.assertIn(("--permission-mode", "manual"),
                      list(zip(el.LAUNCH_ARGV, el.LAUNCH_ARGV[1:])))

    def test_mutant_prompting_tool_removed_trips(self):
        d = json.loads(json.dumps(self.settings))
        d["permissions"]["allow"].remove("Bash")
        self.assertIn("not pre-approved: Bash",
                      preapproval_gaps(d, self.commands))

    def test_mutant_card_tool_pre_approved_trips(self):
        d = json.loads(json.dumps(self.settings))
        d["permissions"]["allow"].append("AskUserQuestion")
        self.assertIn("pre-approved beyond the review commands: AskUserQuestion",
                      preapproval_gaps(d, self.commands))

    def test_mutant_broader_allow_trips(self):
        for extra in ("WebFetch", "TodoWrite", "Skill"):
            with self.subTest(extra=extra):
                d = json.loads(json.dumps(self.settings))
                d["permissions"]["allow"].append(extra)
                self.assertNotEqual(preapproval_gaps(d, self.commands), [])
        d = json.loads(json.dumps(self.settings))
        d["permissions"]["deny"].remove("WebSearch")
        self.assertIn("WebSearch not denied", preapproval_gaps(d, self.commands))


class TestSameModeAsB3(unittest.TestCase):
    """holdout-eval and B3 use one permission mode and one pre-approved tool
    list; the launcher refuses any other at build time."""

    def setUp(self):
        with open(REAL_TEMPLATE, encoding="utf-8") as fh:
            self.settings = json.load(fh)
        with open(B3_RUNBOOK, encoding="utf-8") as fh:
            self.runbook = fh.read()

    def test_launcher_matches_b3_and_the_settings(self):
        self.assertEqual(same_mode_as_b3_problems(el.LAUNCH_ARGV, self.runbook,
                                                  self.settings), [])
        self.assertEqual([m for _n, m, _t in b3_launch_lines(self.runbook)],
                         ["manual", "manual"])

    def test_check_launch_argv_refuses_other_modes_and_lists(self):
        good = el.build_argv("/p", "/s", "m", "/c/H-00000000", "sid")
        el.check_launch_argv(good)

        def swap(old, new):
            i = good.index(old)
            return good[:i] + [new] + good[i + 1:]
        bad = {"dontAsk": swap("manual", "dontAsk"),
               "bypass": swap("manual", "bypass" + "Permissions"),
               "wider": swap(el.SESSION_TOOLS, el.SESSION_TOOLS + ",WebFetch"),
               "narrower": swap(el.SESSION_TOOLS, "Bash"),
               "no list": [a for a in good if a not in ("--allowedTools",
                                                        el.SESSION_TOOLS)],
               "two lists": good + ["--allowedTools", el.SESSION_TOOLS],
               "two modes": good + ["--permission-mode", "manual"]}
        for label, argv in bad.items():
            with self.subTest(label=label):
                with self.assertRaises(KitError):
                    el.check_launch_argv(argv)

    def test_mutant_dontask_reintroduced(self):
        mutant = tuple("dontAsk" if a == "manual" else a for a in el.LAUNCH_ARGV)
        self.assertNotEqual(mutant, el.LAUNCH_ARGV)
        self.assertIn("holdout launcher uses dontAsk",
                      same_mode_as_b3_problems(mutant, self.runbook, self.settings))
        with mock.patch.object(el, "LAUNCH_ARGV", mutant):
            with self.assertRaises(KitError):
                el.build_argv("/p", "/s", "m", "/c/H-00000000", "sid")

    def test_mutant_tool_list_drifts_from_b3(self):
        for new in (el.SESSION_TOOLS + ",AskUserQuestion", "Bash,Read"):
            with self.subTest(new=new):
                mutant = tuple(new if a == el.SESSION_TOOLS else a
                               for a in el.LAUNCH_ARGV)
                self.assertNotEqual(same_mode_as_b3_problems(
                    mutant, self.runbook, self.settings), [])
                with mock.patch.object(el, "LAUNCH_ARGV", mutant):
                    with self.assertRaises(KitError):
                        el.build_argv("/p", "/s", "m", "/c/H-00000000", "sid")


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
        mutant = text.replace(old, old + "        spawn([], {}, run_dir, None)\n")
        self.assertFalse(check_precedes_spawn_holds(mutant))


if __name__ == "__main__":
    unittest.main()
