"""Tests for freeze_check: the pristine fixture passes every runner profile,
each of the 24 environment mutants stops naming its difference, the
candidate guard trips on a covered descendant commit, the production CLI
shapes pass and fail as recorded, and there is no override."""

import ast
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import freeze_check as fc  # noqa: E402
import freeze_manifest as fm  # noqa: E402
import test_freeze_manifest as tfm  # noqa: E402
from freeze_common import FreezeError  # noqa: E402

FC_PY = os.path.join(HERE, "freeze_check.py")
REAL_MAP = os.path.join(os.path.dirname(HERE), "PATH-MAP.json")
HEX64 = r"[0-9a-f]{64}"
HEX40 = r"[0-9a-f]{40}"
B3_MODEL = "claude-fable-5-1[1m]"
RUNBOOK = "docs/design/reachability-dev/RUN-PHASE54-live.md"
HARNESS_MODEL = "claude-fixture-1[1m]"

# The exact identity-bearing CLI shapes each production launcher runs. No
# home, codex-home, manifest or repo flag: production resolves the real home
# and the active manifest of the checkout.
VALIDATION_COMMANDS = {
    "b3": ["verify", "--runner", "b3", "--plugin-dir", "<PLUGIN_DIR>",
           "--settings", "<SETTINGS>",
           "--model", "<runners.b3.launch_model.value>",
           "--clone-dir", "<CLONE_DIR>"],
    "fix-harness": ["verify", "--runner", "fix-harness",
                    "--plugin-dir", "<PLUGIN_DIR>",
                    "--harness-venv", "<HARNESS_VENV>",
                    "--model", "<runners.fix-harness.launch_model.value>"],
    "holdout-autopilot": ["verify", "--runner", "holdout-autopilot"],
    "holdout-eval": ["verify", "--runner", "holdout-eval",
                     "--plugin-dir", "<PLUGIN_DIR>", "--settings", "<SETTINGS>",
                     "--model", "<runners.holdout-eval.launch_model.value>"],
}
# Flags that only say WHERE the active manifest lives; the fixture is not the
# checkout, so tests append them and production appends nothing.
LOCATOR_FLAGS = ("--manifest", "--repo")

RUNNER_TEMPLATE = {
    "model": B3_MODEL,
    "env": {"DISABLE_AUTOUPDATER": "1", "DISABLE_UPDATES": "1"},
    "enabledPlugins": {"vibe-check@thejuran": False},
    "statusLine": {"type": "command",
                   "command": "<RUNNER>/statusline-capture.sh"},
}


def _git(repo, *argv):
    return subprocess.run(["git", "-C", repo, *argv], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE
                          ).stdout.decode().strip()


def _commit(repo, rel, data, msg="c"):
    tfm._write(repo, rel, data)
    _git(repo, "add", "--", rel)
    _git(repo, "commit", "-q", "-m", msg)


class _CheckFixture(tfm._Fixture):
    """The 54-04 fixture plus: a valid PATH-MAP and a runner settings
    template committed at the candidate, the manifest generated from it, the
    plugin materialized from git, an installed runner settings copy and an
    empty target clone."""

    def __init__(self, path_map=None):
        super().__init__()
        r = self.repo
        with open(REAL_MAP, "r", encoding="utf-8") as fh:
            m = json.load(fh)
        if path_map is not None:
            m["rules"] = path_map
        tfm._write(r, "docs/design/freeze-v2.12/PATH-MAP.json", json.dumps(m))
        tfm._write(r, fm.RUNNER_TEMPLATE, json.dumps(RUNNER_TEMPLATE, indent=2))
        tfm._write(r, RUNBOOK, "# BLOCK: common\nset -e\n# END: common\n")
        _git(r, "add", "-A")
        _git(r, "commit", "-q", "-m", "candidate")
        self.candidate = _git(r, "rev-parse", "HEAD")
        base = self._tmp.name
        self.manifest = self.generate()
        self.manifest_path = os.path.join(base, "FREEZE-MANIFEST-1.json")
        fm.write_manifest(self.manifest_path, self.manifest)
        self.plugin_dir = self.materialize_plugin(self.candidate)
        self.runner_dir = os.path.join(base, "runner")
        self.settings_path = self.install_runner_settings(self.runner_dir)
        self.clone = os.path.join(base, "clone")
        os.makedirs(self.clone)

    def settings(self):
        # `$HOME`-relative hook so a relocated copy of the home projects the
        # same hooks hash and hook-script paths.
        s = super().settings()
        hook = s["hooks"]["PreToolUse"][0]["hooks"][0]
        hook["command"] = hook["command"].replace(self.home, "$HOME")
        return s

    def materialize_plugin(self, rev):
        out = os.path.join(self._tmp.name, "plugin-" + rev[:12])
        os.makedirs(out)
        data = subprocess.run(["git", "-C", self.repo, "archive", rev,
                               fm.PLUGIN_ROOT], check=True,
                              stdout=subprocess.PIPE).stdout
        subprocess.run(["tar", "-x", "-C", out, "--strip-components", "2"],
                       input=data, check=True)
        return out

    def install_runner_settings(self, runner_dir, settings=None):
        os.makedirs(runner_dir, exist_ok=True)
        s = json.loads(json.dumps(settings or RUNNER_TEMPLATE))
        s["statusLine"]["command"] = s["statusLine"]["command"].replace(
            "<RUNNER>", runner_dir)
        path = os.path.join(runner_dir, "settings-measured.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(s, fh, indent=2)
        shutil.copy2(os.path.join(self.repo, fm.RUNNER_STATUSLINE), runner_dir)
        return path

    def edit_settings_copy(self, fn):
        with open(self.settings_path, "r", encoding="utf-8") as fh:
            s = json.load(fh)
        fn(s)
        with open(self.settings_path, "w", encoding="utf-8") as fh:
            json.dump(s, fh)

    def kwargs(self, runner):
        if runner in ("b3", "holdout-eval"):
            kw = {"plugin_dir": self.plugin_dir,
                  "settings_path": self.settings_path, "launch_model": B3_MODEL}
            if runner == "b3":
                kw["clone_dir"] = self.clone
            return kw
        if runner == "fix-harness":
            return {"plugin_dir": self.plugin_dir, "launch_model": HARNESS_MODEL,
                    "harness_venv": self.venv}
        return {}

    def check(self, runner, **over):
        kw = {"repo": self.repo, "env": {}, "home": self.home,
              "codex_home": self.codex_home}
        kw.update(self.kwargs(runner))
        kw.update(over)
        with mock.patch.dict(os.environ, self.path_env()):
            return fc.verify(self.manifest, runner, **kw)

    def drifted_home(self):
        """A copy of the fixture home whose settings gained one
        permissions.allow entry."""
        copy = os.path.join(self._tmp.name, "home-drift")
        shutil.copytree(self.home, copy, symlinks=True)
        s = self.settings()
        s["permissions"]["allow"].append("Bash(ls)")
        tfm._write(copy, ".claude/settings.json", json.dumps(s))
        return copy

    def cli_env(self, home=None):
        return {"PATH": self.bin + os.pathsep + os.environ.get("PATH", ""),
                "HOME": home or self.home}

    def run_cli(self, argv, home=None):
        proc = subprocess.run([sys.executable, FC_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=self.cli_env(home), timeout=120)
        return proc.returncode, proc.stdout.decode(), proc.stderr.decode()


class _Base(unittest.TestCase):
    def setUp(self):
        self.fx = _CheckFixture()
        self.addCleanup(self.fx.close)

    def pristine(self, runner):
        result = self.fx.check(runner)
        self.assertEqual(result.problems, [], runner)
        return result

    def stops(self, runner, prefix, **over):
        problems = self.fx.check(runner, **over).problems
        self.assertTrue(any(p.startswith(prefix) for p in problems),
                        "%r not in %r" % (prefix, problems))
        return problems


# --------------------------------------------------------------------------- #
# Pristine
# --------------------------------------------------------------------------- #

class TestPristine(_Base):
    def test_every_runner_passes(self):
        for runner in fc.RUNNERS:
            self.pristine(runner)

    def test_stamp_lines(self):
        result = self.pristine("b3")
        lines = fc.stamp_lines(result)
        self.assertEqual(len(lines), 3)
        self.assertRegex(lines[0], "^manifest_id: %s$" % HEX64)
        self.assertRegex(lines[1], "^check_digest: %s$" % HEX64)
        self.assertRegex(lines[2], "^candidate_sha: %s$" % HEX40)
        self.assertEqual(result.manifest_id, self.fx.manifest["manifest_id"])
        self.assertEqual(result.candidate_sha, self.fx.candidate)

    def test_check_digest_tracks_observation(self):
        first = self.pristine("b3").check_digest
        self.assertEqual(self.pristine("b3").check_digest, first)
        tfm._write(self.fx.plugin_dir, "agents/a.md", "changed\n")
        self.assertNotEqual(self.fx.check("b3").check_digest, first)

    def test_cli_exit_0(self):
        code, out, _ = self.fx.run_cli(
            ["verify", "--runner", "holdout-autopilot", "--manifest",
             self.fx.manifest_path, "--repo", self.fx.repo])
        self.assertEqual(code, 0, out)
        self.assertRegex(out.strip(), "^IDENTITY OK manifest_id=%s check_digest=%s "
                                      "candidate_sha=%s$" % (HEX64, HEX64, HEX40))


# --------------------------------------------------------------------------- #
# Mutation matrix
# --------------------------------------------------------------------------- #

class TestMutants(_Base):
    def test_mutant_01_file_differs(self):
        self.pristine("b3")
        with open(os.path.join(self.fx.plugin_dir, "agents/a.md"), "ab") as fh:
            fh.write(b"x")
        problems = self.stops("b3", "file differs: agents/a.md (manifest ")
        self.assertFalse(any(p.startswith("setting differs") for p in problems))

    def test_mutant_02_file_extra(self):
        self.pristine("b3")
        tfm._write(self.fx.plugin_dir, "skills/x/SKILL.md", "extra\n")
        self.stops("b3", "file extra: skills/x/SKILL.md")

    def test_mutant_03_file_missing(self):
        self.pristine("b3")
        os.remove(os.path.join(self.fx.plugin_dir, "scripts/x.py"))
        self.stops("b3", "file missing: scripts/x.py")

    def test_mutant_04_mode(self):
        self.pristine("b3")
        os.chmod(os.path.join(self.fx.plugin_dir, "scripts/x.py"), 0o755)
        self.stops("b3", "file differs: scripts/x.py (mode manifest 100644 "
                         "live 100755)")

    def test_mutant_05_env_alias(self):
        self.pristine("b3")
        s = self.fx.settings()
        s["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] = "claude-opus-5-5"
        self.fx.write_settings(s)
        problems = self.stops("b3", "setting differs: env.ANTHROPIC_DEFAULT_OPUS_MODEL "
                                    "(manifest claude-opus-5-5[1m] live "
                                    "claude-opus-5-5)")
        self.assertFalse(any(p.startswith("file ") for p in problems))

    def test_mutant_06_top_env(self):
        self.pristine("b3")
        self.stops("b3", "setting differs: env.VIBE_CHECK_TOP_MODEL "
                         "(manifest null live fable)",
                   env={"VIBE_CHECK_TOP_MODEL": "fable"})

    def test_mutant_07_toml(self):
        self.pristine("b3")
        tfm._write(self.fx.clone, ".vibe-check.toml", 'top_model = "fable"\n')
        self.stops("b3", "setting differs: .vibe-check.toml present")

    def test_mutant_08_codex_effort(self):
        self.pristine("b3")
        tfm._write(self.fx.codex_home, "config.toml",
                   'model = "gpt-x"\nmodel_reasoning_effort = "low"\n'
                   'service_tier = "fast"\napproval_policy = "never"\n')
        self.stops("b3", "setting differs: codex.config.model_reasoning_effort "
                         "(manifest high live low)")

    def test_mutant_09_companion(self):
        self.pristine("b3")
        with open(os.path.join(self.fx.home, ".claude/plugins/cache/codex/README.md"),
                  "ab") as fh:
            fh.write(b"x")
        self.stops("b3", "file differs: codex-companion")

    def test_mutant_10_cli_version(self):
        self.pristine("b3")
        tfm._write(self.fx.bin, "claude", "#!/bin/sh\necho '9.9.10 (Claude Code)'\n",
                   mode=0o755)
        self.stops("b3", "version differs: claude-code (manifest 9.9.9 live 9.9.10)")

    def test_mutant_11_cli_binary(self):
        self.pristine("holdout-autopilot")
        tfm._write(self.fx.bin, "claude",
                   "#!/bin/sh\n# rebuilt\necho '9.9.9 (Claude Code)'\n", mode=0o755)
        problems = self.stops("holdout-autopilot",
                              "binary differs: claude-code (same version string")
        self.assertFalse(any(p.startswith("version differs") for p in problems))

    def test_mutant_12_bundled_cli(self):
        self.pristine("fix-harness")
        site = os.path.join(self.fx.venv, "lib", "python3.14", "site-packages")
        tfm._write(site, "claude_agent_sdk/_bundled/claude",
                   "#!/bin/sh\n# rebuilt\necho '2.1.294 (Claude Code)'\n", mode=0o755)
        self.stops("fix-harness", "binary differs: agent-sdk-bundled-claude "
                                  "(same version string")

    def test_mutant_13_kit_tree(self):
        self.pristine("fix-harness")
        with open(os.path.join(self.fx.repo, "docs/design/fix-harness/tools/t.py"),
                  "ab") as fh:
            fh.write(b"#")
        self.stops("fix-harness", "file differs: fix-harness/tools/t.py")

    def test_mutant_14_covered_commit(self):
        self.pristine("b3")
        _commit(self.fx.repo, "plugins/vibe-check/scripts/x.py", "print(9)\n")
        self.stops("b3", "repo: non-reporting change after candidate: "
                         "plugins/vibe-check/scripts/x.py [")

    def test_mutant_15_unmapped_commit(self):
        self.pristine("b3")
        _commit(self.fx.repo, "docs/design/freeze-v2.12/evidence/x.md", "ev\n")
        self.pristine("b3")  # D-18: reporting-only commit
        _commit(self.fx.repo, "docs/other/y.md", "y\n")
        self.stops("b3", "repo: non-reporting change after candidate: "
                         "docs/other/y.md [engineering, detection, workflow]")

    def test_mutant_16_manifest_tamper(self):
        self.assertEqual(fc.load_manifest(self.fx.manifest_path)["manifest_id"],
                         self.fx.manifest["manifest_id"])
        m = json.loads(json.dumps(self.fx.manifest))
        m["plugin"]["files"]["agents/a.md"]["sha256"] = "0" * 64
        bad = os.path.join(self.fx._tmp.name, "FREEZE-MANIFEST-2.json")
        with open(bad, "w", encoding="utf-8") as fh:
            json.dump(m, fh)
        with self.assertRaises(FreezeError) as cm:
            fc.load_manifest(bad)
        self.assertIn(bad, str(cm.exception))
        code, out, err = self.fx.run_cli(["verify", "--runner", "holdout-autopilot",
                                          "--manifest", bad, "--repo", self.fx.repo])
        self.assertEqual(code, 2)
        self.assertIn(bad, err)
        self.assertNotIn("IDENTITY OK", out)

    def test_mutant_17_permissions(self):
        self.pristine("b3")
        for mutate in (lambda p: p["allow"].append("Bash(ls)"),
                       lambda p: p.__setitem__("defaultMode", "acceptEdits"),
                       lambda p: p["additionalDirectories"].append("/tmp/y")):
            s = self.fx.settings()
            mutate(s["permissions"])
            self.fx.write_settings(s)
            problems = self.fx.check("b3").problems
            settings_lines = [p for p in problems if p.startswith("setting differs:")]
            self.assertEqual(settings_lines, ["setting differs: permissions"])
        self.fx.write_settings(self.fx.settings())
        self.pristine("b3")

    def test_mutant_18_harness_env(self):
        self.pristine("fix-harness")
        problems = self.stops("fix-harness",
                              "setting differs: env.ANTHROPIC_MODEL "
                              "(manifest null live claude-x)",
                              env={"ANTHROPIC_MODEL": "claude-x"})
        self.assertFalse(any(p.startswith("file differs:") for p in problems))

    def test_mutant_19_harness_model(self):
        self.pristine("fix-harness")
        self.stops("fix-harness", "setting differs: launch_model (manifest %s live "
                                  "claude-other)" % HARNESS_MODEL,
                   launch_model="claude-other")
        self.stops("fix-harness", "setting differs: launch_model (manifest %s live "
                                  "null)" % HARNESS_MODEL, launch_model=None)

    def test_mutant_20_runner_settings_plugins(self):
        self.pristine("b3")
        self.fx.edit_settings_copy(
            lambda s: s["enabledPlugins"].__setitem__("vibe-check@thejuran", True))
        problems = self.stops(
            "b3", "setting differs: runner-settings.enabledPlugins.vibe-check@thejuran")
        self.assertFalse(any(p.startswith("file differs:") for p in problems))
        self.assertIn("setting differs: runner-settings.enabledPlugins."
                      "vibe-check@thejuran",
                      self.stops("holdout-eval", "setting differs: runner-settings"))

    def test_mutant_21_runner_settings_env(self):
        self.pristine("b3")
        cases = (
            (lambda s: s["env"].__setitem__("ANTHROPIC_MODEL", "x"), "env.ANTHROPIC_MODEL"),
            (lambda s: s.__setitem__("permissions", {"allow": ["Bash"]}), "permissions"),
            (lambda s: s.__setitem__("hooks", {"Stop": []}), "hooks"),
            (lambda s: s.__setitem__("model", "claude-other"), "model"),
        )
        for mutate, key in cases:
            self.fx.install_runner_settings(self.fx.runner_dir)
            self.pristine("b3")
            self.fx.edit_settings_copy(mutate)
            problems = self.fx.check("b3").problems
            self.assertIn("setting differs: runner-settings." + key, problems)

    def test_mutant_22_runner_settings_missing(self):
        self.pristine("b3")
        self.stops("b3", fc.SETTINGS_MISSING, settings_path=None)
        self.stops("holdout-eval", fc.SETTINGS_MISSING, settings_path=None)
        with open(os.path.join(self.fx.runner_dir, "statusline-capture.sh"),
                  "ab") as fh:
            fh.write(b"#")
        self.stops("b3", "file differs: runner-settings.statusLine script")

    def test_mutant_23_covered_artifact_head(self):
        self.pristine("b3")
        _commit(self.fx.repo, "plugins/vibe-check/scripts/x.py", "print(9)\n")
        problems = self.fx.check("b3").problems
        self.assertTrue(any(p.startswith("repo: non-reporting change after candidate: "
                                         "plugins/vibe-check/scripts/x.py")
                            for p in problems))
        self.assertIn("repo: covered artifact differs at HEAD: "
                      "plugins/vibe-check/scripts/x.py", problems)

    def test_mutant_23_covered_artifact_head_with_lax_map(self):
        fx = _CheckFixture(path_map=[{"glob": "**", "cats": ["reporting"]}])
        self.addCleanup(fx.close)
        self.assertEqual(fx.check("b3").problems, [])
        _commit(fx.repo, "plugins/vibe-check/scripts/x.py", "print(9)\n")
        problems = fx.check("b3").problems
        self.assertFalse(any(p.startswith("repo: non-reporting") for p in problems))
        self.assertIn("repo: covered artifact differs at HEAD: "
                      "plugins/vibe-check/scripts/x.py", problems)

    def test_mutant_24_home_default(self):
        fx = self.fx
        base = fx.path_env()
        fx_env = {"repo": fx.repo, "env": {}}
        fx_env.update(fx.kwargs("b3"))
        drift = fx.drifted_home()
        for home, want in ((fx.home, []), (drift, ["setting differs: permissions"])):
            env = dict(base, HOME=home)
            with mock.patch.dict(os.environ, env):
                os.environ.pop("CODEX_HOME", None)
                problems = fc.verify(fx.manifest, "b3", home=None, **fx_env).problems
            self.assertEqual(problems, want)
            argv = self.cli_shape(fx, "b3")
            code, out, _ = fx.run_cli(argv, home=home)
            self.assertEqual(code, 1 if want else 0, out)
            if want:
                self.assertIn("setting differs: permissions", out)

    @staticmethod
    def cli_shape(fx, runner):
        return _shape(fx, VALIDATION_COMMANDS[runner]) + [
            "--manifest", fx.manifest_path, "--repo", fx.repo]


def _shape(fx, argv):
    subs = {"<PLUGIN_DIR>": fx.plugin_dir, "<SETTINGS>": fx.settings_path,
            "<CLONE_DIR>": fx.clone, "<HARNESS_VENV>": fx.venv}
    out = []
    for a in argv:
        m = re.match(r"^<(runners\.[a-z0-9-]+\.launch_model\.value)>$", a)
        if m:
            node = fx.manifest
            for part in m.group(1).split("."):
                node = node[part]
            out.append(node)
        else:
            out.append(subs.get(a, a))
    return out


def _drop(argv, flag):
    i = argv.index(flag)
    return argv[:i] + argv[i + 2:]


# --------------------------------------------------------------------------- #
# Candidate guard
# --------------------------------------------------------------------------- #

class TestCandidateGuard(_Base):
    def guard_cli(self):
        return self.fx.run_cli(["candidate-guard", "--candidate", self.fx.candidate,
                                "--repo", self.fx.repo])

    def test_reporting_descendant_passes(self):
        _commit(self.fx.repo, "docs/design/freeze-v2.12/evidence/x.json", "{}\n")
        self.assertEqual(fc.candidate_guard(self.fx.repo, self.fx.candidate), [])
        code, out, _ = self.guard_cli()
        self.assertEqual(code, 0, out)
        self.assertRegex(out.strip(), "^CANDIDATE OK candidate=%s head=%s "
                                      "descendant_commits=1 \\(reporting-only\\)$"
                         % (self.fx.candidate, HEX40))

    def test_covered_descendant_stops(self):
        _commit(self.fx.repo, "plugins/vibe-check/agents/a.md", "changed\n")
        problems = fc.candidate_guard(self.fx.repo, self.fx.candidate)
        self.assertTrue(any("plugins/vibe-check/agents/a.md" in p for p in problems))
        self.assertIn("repo: covered artifact differs at HEAD: "
                      "plugins/vibe-check/agents/a.md", problems)
        code, out, _ = self.guard_cli()
        self.assertEqual(code, 1)
        self.assertEqual(out.strip().splitlines()[-1], fc.MOVED_LINE)

    def test_head_not_descendant(self):
        _git(self.fx.repo, "checkout", "-q", "-b", "side", self.fx.candidate + "~1")
        _commit(self.fx.repo, "docs/design/freeze-v2.12/evidence/z.md", "z\n")
        problems = fc.candidate_guard(self.fx.repo, self.fx.candidate)
        self.assertTrue(any("is not a descendant of candidate" in p for p in problems))

    def test_uncommitted_covered_change(self):
        with open(os.path.join(self.fx.repo, "plugins/vibe-check/scripts/x.py"),
                  "ab") as fh:
            fh.write(b"#")
        self.assertIn("repo: uncommitted change in covered path: "
                      "plugins/vibe-check/scripts/x.py",
                      fc.candidate_guard(self.fx.repo, self.fx.candidate))

    def test_uncovered_working_tree_edit_passes(self):
        tfm._write(self.fx.repo, "notes/scratch.md", "x\n")
        self.assertEqual(fc.candidate_guard(self.fx.repo, self.fx.candidate), [])

    def test_guard_has_no_override(self):
        p = fc.build_parser()
        guard = p._subparsers._group_actions[0].choices["candidate-guard"]
        self.assertEqual(sorted(o for o in guard.option_string_actions
                                if o.startswith("--")),
                         ["--candidate", "--help", "--repo"])


# --------------------------------------------------------------------------- #
# Production CLI shapes
# --------------------------------------------------------------------------- #

class TestValidationCommands(_Base):
    def run_shape(self, runner, argv=None, home=None):
        argv = _shape(self.fx, argv or VALIDATION_COMMANDS[runner])
        return self.fx.run_cli(argv + ["--manifest", self.fx.manifest_path,
                                       "--repo", self.fx.repo], home=home)

    def test_validation_commands_have_no_home_flag(self):
        for argv in VALIDATION_COMMANDS.values():
            for flag in ("--home", "--codex-home") + LOCATOR_FLAGS:
                self.assertNotIn(flag, argv)
        self.assertEqual(set(VALIDATION_COMMANDS), set(fc.RUNNERS))

    def test_validation_commands_pass_on_fixture(self):
        for runner in fc.RUNNERS:
            code, out, err = self.run_shape(runner)
            self.assertEqual(code, 0, (runner, out, err))
            self.assertTrue(out.startswith("IDENTITY OK "), out)

    def test_validation_commands_without_model_stop(self):
        for runner in ("b3", "fix-harness", "holdout-eval"):
            code, out, _ = self.run_shape(runner,
                                          _drop(VALIDATION_COMMANDS[runner], "--model"))
            self.assertEqual(code, 1, (runner, out))
            self.assertIn("setting differs: launch_model", out)
            self.assertEqual(out.strip().splitlines()[-1], fc.MISMATCH_LINE)

    def test_validation_commands_without_settings_stop(self):
        for runner in ("b3", "holdout-eval"):
            code, out, _ = self.run_shape(
                runner, _drop(VALIDATION_COMMANDS[runner], "--settings"))
            self.assertEqual(code, 1, (runner, out))
            self.assertIn(fc.SETTINGS_MISSING, out)

    def test_validation_commands_default_home_drift_stops(self):
        drift = self.fx.drifted_home()
        for runner in ("b3", "holdout-eval"):
            code, out, _ = self.run_shape(runner, home=drift)
            self.assertEqual(code, 1, (runner, out))
            self.assertIn("setting differs: permissions", out)


# --------------------------------------------------------------------------- #
# No override, version is not identity, CLI, import lock
# --------------------------------------------------------------------------- #

OVERRIDE_RE = re.compile(r"force|skip|override|allow|ignore|disable|bypass",
                         re.IGNORECASE)


class TestNoOverride(unittest.TestCase):
    def test_parser_has_no_override_option(self):
        p = fc.build_parser()
        for sub in p._subparsers._group_actions[0].choices.values():
            for opt in sub.option_string_actions:
                self.assertIsNone(OVERRIDE_RE.search(opt), opt)

    def test_verify_has_no_class_disabling_keyword(self):
        params = set(inspect.signature(fc.verify).parameters)
        self.assertEqual(params, {"manifest", "runner", "plugin_dir", "settings_path",
                                  "launch_model", "clone_dir", "repo", "env", "home",
                                  "codex_home", "harness_venv"})
        for name in params:
            self.assertIsNone(OVERRIDE_RE.search(name), name)

    def test_unknown_runner_refused(self):
        with self.assertRaises(FreezeError):
            fc.verify({"manifest_id": "0" * 64, "candidate_sha": "0" * 40}, "other")

    def test_every_profile_class_has_a_check(self):
        for runner in fc.RUNNERS:
            for name in fc.PROFILE_CLASSES[runner]:
                self.assertIn(name, fc.CHECKS)
            self.assertIn("repo_state", fc.PROFILE_CLASSES[runner])
        self.assertIn("process_env", fc.PROFILE_CLASSES["fix-harness"])
        self.assertIn("launch_model", fc.PROFILE_CLASSES["fix-harness"])


class TestVersionIsNotIdentity(_Base):
    def test_matching_version_with_differing_byte_stops(self):
        self.pristine("b3")
        with open(os.path.join(self.fx.plugin_dir, "agents/a.md"), "ab") as fh:
            fh.write(b"x")
        tfm._write(self.fx.plugin_dir, ".claude-plugin/plugin.json",
                   '{"version": "2.12.0"}\n')
        result = self.fx.check("b3")
        self.assertEqual(result.observed["plugin_files"]["plugin_json_version"],
                         self.fx.manifest["plugin"]["plugin_json_version"])
        self.assertTrue(any(p.startswith("file differs: agents/a.md")
                            for p in result.problems))

    def test_collector_failure_fails_closed(self):
        self.pristine("b3")
        with mock.patch.object(fm, "_native_cli", side_effect=RuntimeError("boom")):
            problems = self.fx.check("b3").problems
        self.assertIn("observe failed: native_cli: RuntimeError", problems)


class TestCLI(_Base):
    def base(self, runner="b3"):
        return TestMutants.cli_shape(self.fx, runner)

    def test_exit_1_lists_differences_then_stops(self):
        tfm._write(self.fx.plugin_dir, "skills/x/SKILL.md", "extra\n")
        code, out, _ = self.fx.run_cli(self.base())
        self.assertEqual(code, 1)
        lines = out.strip().splitlines()
        self.assertIn("file extra: skills/x/SKILL.md", lines)
        self.assertEqual(lines[-1], "IDENTITY MISMATCH — STOPPING")

    def test_exit_2_usage_and_unreadable(self):
        self.assertEqual(self.fx.run_cli(["verify", "--runner", "nope"])[0], 2)
        self.assertEqual(self.fx.run_cli(["verify"])[0], 2)
        self.assertEqual(self.fx.run_cli(["verify", "--runner", "b3", "--force"])[0], 2)
        code, out, _ = self.fx.run_cli(["verify", "--runner", "b3", "--manifest",
                                        "/nonexistent.json"])
        self.assertEqual(code, 2)
        self.assertNotIn("IDENTITY OK", out)

    def test_active_manifest_highest_n(self):
        d = os.path.join(self.fx.repo, fc.MANIFEST_DIR)
        for n in (2, 10):
            tfm._write(d, "FREEZE-MANIFEST-%d.json" % n, "{}\n")
        self.assertTrue(fc.active_manifest(self.fx.repo).endswith(
            "FREEZE-MANIFEST-10.json"))
        with self.assertRaises(FreezeError):
            fc.active_manifest(os.path.join(self.fx._tmp.name, "empty"))


# --------------------------------------------------------------------------- #
# The B3 live-check runbook is covered (D-18: Markdown the runner executes)
# --------------------------------------------------------------------------- #

class TestRunbookCovered(_Base):
    def test_runbook_in_covered_file_map(self):
        self.assertIn((RUNBOOK, None), fm.COVERED)
        self.assertIn(RUNBOOK, fc.B3_COVERED_KEYS)
        files = self.fx.manifest["covered"][RUNBOOK]["files"]
        self.assertEqual(set(files), {"RUN-PHASE54-live.md"})
        self.assertRegex(files["RUN-PHASE54-live.md"]["sha256"], r"^[0-9a-f]{64}$")

    def test_real_runbook_hashed_from_git(self):
        if tfm.REAL_REPO is None:
            self.skipTest("not in a git checkout")
        cov = fm.covered_tree_files(tfm.REAL_REPO, "HEAD")
        self.assertEqual(set(cov[RUNBOOK]["files"]), {"RUN-PHASE54-live.md"})

    def test_real_map_classifies_runbook_like_the_runner_layer(self):
        import freeze_policy
        with open(REAL_MAP, "r", encoding="utf-8") as fh:
            pm = freeze_policy.validate_path_map(json.load(fh))
        got = freeze_policy.classify(
            [RUNBOOK, "docs/design/b3-ground-truth/b3-runner-v2.12/common.sh",
             "docs/design/reachability-dev/NOTES-phase54-live.md",
             "docs/design/reachability-dev/runs-phase54-live/c/run-1/state.json",
             "docs/design/freeze-v2.12/evidence/x.json"], pm)
        self.assertEqual(got[RUNBOOK],
                         got["docs/design/b3-ground-truth/b3-runner-v2.12/common.sh"])
        self.assertTrue(got[RUNBOOK] & set(freeze_policy.RERUN_CATEGORIES))
        for path in ("docs/design/reachability-dev/NOTES-phase54-live.md",
                     "docs/design/reachability-dev/runs-phase54-live/c/run-1/state.json",
                     "docs/design/freeze-v2.12/evidence/x.json"):
            self.assertEqual(got[path], {"reporting"}, path)
        rules = [r["glob"] for r in json.load(open(REAL_MAP, encoding="utf-8"))["rules"]]
        self.assertIn(RUNBOOK, rules)

    def test_committed_runbook_change_stops(self):
        self.pristine("b3")
        _commit(self.fx.repo, RUNBOOK, "# BLOCK: common\nset +e\n# END: common\n")
        problems = self.fx.check("b3").problems
        self.assertIn("repo: covered artifact differs at HEAD: " + RUNBOOK, problems)
        self.assertTrue(any(p.startswith("repo: non-reporting change after candidate: "
                                         + RUNBOOK) for p in problems), problems)
        self.assertTrue(any(p.startswith("file differs: reachability-dev/RUN-PHASE54-live.md")
                            for p in problems), problems)
        self.assertIn("repo: covered artifact differs at HEAD: " + RUNBOOK,
                      fc.candidate_guard(self.fx.repo, self.fx.candidate))

    def test_runbook_change_stops_even_under_a_lax_map(self):
        fx = _CheckFixture(path_map=[{"glob": "**", "cats": ["reporting"]}])
        self.addCleanup(fx.close)
        self.assertEqual(fx.check("b3").problems, [])
        _commit(fx.repo, RUNBOOK, "# BLOCK: common\nset +e\n# END: common\n")
        problems = fx.check("b3").problems
        self.assertFalse(any(p.startswith("repo: non-reporting") for p in problems))
        self.assertIn("repo: covered artifact differs at HEAD: " + RUNBOOK, problems)

    def test_uncommitted_runbook_edit_stops(self):
        self.pristine("b3")
        with open(os.path.join(self.fx.repo, RUNBOOK), "ab") as fh:
            fh.write(b"#")
        problems = self.fx.check("b3").problems
        self.assertIn("repo: uncommitted change in covered path: " + RUNBOOK, problems)

    def test_reporting_neighbours_stay_exempt(self):
        self.pristine("b3")
        _commit(self.fx.repo, "docs/design/reachability-dev/NOTES-phase54-live.md", "n\n")
        _commit(self.fx.repo,
                "docs/design/reachability-dev/runs-phase54-live/c/run-1/state.json", "{}\n")
        self.pristine("b3")


class TestImportSet(unittest.TestCase):
    def test_imports(self):
        with open(FC_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module.split(".")[0])
        allowed = {"argparse", "hashlib", "json", "os", "re", "subprocess", "sys",
                   "freeze_common", "freeze_policy", "freeze_manifest"}
        self.assertLessEqual(names, allowed)


if __name__ == "__main__":
    unittest.main()
