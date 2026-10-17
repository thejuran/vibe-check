"""Tests for freeze_manifest: generation from a git fixture, the manifest
schema, secret refusal, verify-self tamper detection, the CLI, the import
lock and a mutation matrix proving each guard can trip."""

import ast
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import freeze_common  # noqa: E402
import freeze_manifest as fm  # noqa: E402
from freeze_common import FreezeError  # noqa: E402

FM_PY = os.path.join(HERE, "freeze_manifest.py")
CLOCK = lambda: 1760000000  # noqa: E731
HOOK_GHP = "ghp_examplevalue"
HOOK_UNPREFIXED = "example-unprefixed-secret-value"
PLANTED_KEY = "sk-ant-planted-example-0000"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _repo_root():
    try:
        out = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=30)
    except OSError:
        return None
    return out.stdout.decode().strip() if out.returncode == 0 else None


REAL_REPO = _repo_root()


def _run(cwd, *argv):
    subprocess.run(list(argv), cwd=cwd, check=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)


def _write(root, rel, data, mode=None):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    if mode is not None:
        os.chmod(path, mode)
    return path


def _strings(value, out=None):
    """Every string leaf AND every dict key in `value`."""
    out = [] if out is None else out
    if isinstance(value, dict):
        for k, v in value.items():
            out.append(str(k))
            _strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _strings(v, out)
    elif isinstance(value, str):
        out.append(value)
    return out


class _Fixture:
    """A temp git repo, a fake home, fake CLIs and a fake harness venv."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = self._tmp.name
        self.repo = os.path.join(base, "repo")
        self.home = os.path.join(base, "home")
        self.bin = os.path.join(base, "bin")
        self.venv = os.path.join(base, "venv")
        self.codex_home = os.path.join(self.home, ".codex")
        self._build_repo()
        self._build_home()
        self._build_bins()

    def close(self):
        self._tmp.cleanup()

    # repo ------------------------------------------------------------------
    def _build_repo(self):
        r = self.repo
        os.makedirs(r)
        _run(r, "git", "init", "-q")
        _run(r, "git", "config", "user.email", "t@example.invalid")
        _run(r, "git", "config", "user.name", "t")
        p = "plugins/vibe-check/"
        _write(r, p + ".claude-plugin/plugin.json", '{"version": "2.12.0"}\n')
        _write(r, p + "agents/a.md", "---\nname: a\nmodel: opus\n---\nbody\n")
        _write(r, p + "agents/index.md", "# Agents\n\nmodel: sonnet\n")
        _write(r, p + "agents/secret-handling.md", "no frontmatter\n")
        _write(r, p + "scripts/x.py", "print(1)\n")
        _write(r, p + "scripts/token_counter.py", "print(2)\n")
        _write(r, p + "docs/efficacy/ANSWER-KEY.md", "key\n")
        _write(r, "docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md", "answers\n")
        _write(r, "docs/design/fix-harness/tools/t.py", "print(3)\n")
        _write(r, "docs/design/fix-harness/requirements.txt",
               "# harness only\nclaude-agent-sdk==0.2.165\n")
        _write(r, "docs/design/fix-harness/fixtures/probe/sandbox-probe.json",
               json.dumps({"passed": True, "model": "claude-fixture-1[1m]",
                           "settings_fingerprint": "ab" * 32}))
        _write(r, "docs/design/holdout-v2.12/tools/h.py", "print(4)\n")
        _write(r, "docs/design/freeze-v2.12/PATH-MAP.json", "{}\n")
        _write(r, "docs/design/freeze-v2.12/tools/FREEZE-MANIFEST-1.json", "{}\n")
        _write(r, "docs/design/freeze-v2.12/FREEZE-MANIFEST-1.json", "{}\n")
        _run(r, "git", "add", "-A")
        _run(r, "git", "commit", "-q", "-m", "c1")
        self.template = {"model": "claude-fable-5-1[1m]",
                         "statusLine": {"type": "command",
                                        "command": "<RUNNER>/statusline-capture.sh"}}
        _write(r, fm.RUNNER_TEMPLATE, json.dumps(self.template, indent=2))
        _write(r, fm.RUNNER_STATUSLINE, "#!/bin/sh\ncat\n", mode=0o755)
        _run(r, "git", "add", "-A")
        _run(r, "git", "commit", "-q", "-m", "c2")

    # home ------------------------------------------------------------------
    def settings(self):
        hook = os.path.join(self.home, ".claude", "hooks", "h.sh")
        return {
            "env": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5[1m]",
                    "ANTHROPIC_BASE_URL": "http://127.0.0.1:18764",
                    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000",
                    "DISABLE_AUTOUPDATER": "1",
                    "ANTHROPIC_API_KEY": PLANTED_KEY},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{
                "type": "command",
                "command": 'bash "%s" %s --token %s'
                           % (hook, HOOK_GHP, HOOK_UNPREFIXED)}]}]},
            "enabledPlugins": {"p@m": True, "off@m": False},
            "permissions": {"allow": ["Bash(git status)"], "deny": ["Read(./.env)"],
                            "additionalDirectories": ["/tmp/x"],
                            "defaultMode": "default"},
            "effortLevel": "xhigh",
            "modelSettings": {"claude-fable-5-1": {"effortLevel": "medium"}},
            "alwaysThinkingEnabled": False,
            "theme": "dark",
            "tui": {"x": 1},
        }

    def write_settings(self, settings):
        _write(self.home, ".claude/settings.json", json.dumps(settings))

    def _build_home(self):
        h = self.home
        self.write_settings(self.settings())
        _write(h, ".claude/hooks/h.sh", "#!/bin/sh\nexit 0\n", mode=0o755)
        _write(h, ".claude/CLAUDE.md", "global instructions\n")
        plugins = {}
        for name, d in (("p@m", "p"), ("off@m", "off"),
                        ("codex@openai-codex", "codex"),
                        ("model-gateway@eigenwise-toolshed", "gw")):
            path = os.path.join(h, ".claude/plugins/cache", d)
            _write(path, "README.md", name + "\n")
            plugins[name] = [{"scope": "user", "installPath": path,
                              "version": "1.0.0", "gitCommitSha": "a" * 40}]
        _write(os.path.join(h, ".claude/plugins/cache/gw"), "package.json",
               '{"version": "0.51.2"}')
        _write(h, ".claude/plugins/installed_plugins.json",
               json.dumps({"version": 2, "plugins": plugins}))
        _write(h, ".codex/config.toml",
               'model = "gpt-x"\nmodel_reasoning_effort = "high"\n'
               'service_tier = "fast"\napproval_policy = "never"\n')

    def _build_bins(self):
        _write(self.bin, "claude", "#!/bin/sh\necho '9.9.9 (Claude Code)'\n", mode=0o755)
        _write(self.bin, "codex", "#!/bin/sh\necho 'codex-cli 1.2.3'\n", mode=0o755)
        site = os.path.join(self.venv, "lib", "python3.14", "site-packages")
        os.makedirs(os.path.join(site, "claude_agent_sdk-0.2.165.dist-info"))
        _write(site, "claude_agent_sdk/_bundled/claude",
               "#!/bin/sh\necho '2.1.294 (Claude Code)'\n", mode=0o755)

    def path_env(self):
        return {"PATH": self.bin + os.pathsep + os.environ.get("PATH", "")}

    def generate(self, repo=None, candidate="HEAD", env=None, **kw):
        kw.setdefault("home", self.home)
        kw.setdefault("codex_home", self.codex_home)
        kw.setdefault("harness_venv", self.venv)
        kw.setdefault("clock", CLOCK)
        with mock.patch.dict(os.environ, self.path_env()):
            return fm.generate(repo or self.repo, candidate,
                               env={} if env is None else env, **kw)


class _Base(unittest.TestCase):
    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.close)

    def gen(self, **kw):
        return self.fx.generate(**kw)


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #

class TestGenerate(_Base):
    def test_plugin_files_equal_git_tree(self):
        m = self.gen()
        self.assertEqual(m["plugin"]["files"], freeze_common.tree_files_at(
            self.fx.repo, "HEAD", "plugins/vibe-check"))
        self.assertEqual(m["plugin"]["file_count"], 7)
        self.assertEqual(m["plugin"]["plugin_json_version"], "2.12.0")

    def test_untracked_plugin_file_not_in_manifest(self):
        _write(self.fx.repo, "plugins/vibe-check/agents/stray.md", "stray\n")
        m = self.gen()
        self.assertNotIn("agents/stray.md", m["plugin"]["files"])

    def test_index_body_pin_ignored(self):
        self.assertEqual(self.gen()["models"]["agent_pins"], {"a": "opus"})

    def test_top_default_and_env(self):
        self.assertEqual(self.gen()["models"]["top"],
                         {"value": "opus", "source": "default"})
        self.assertEqual(self.gen(env={"VIBE_CHECK_TOP_MODEL": "fable"})["models"]["top"],
                         {"value": "fable", "source": "env"})

    def test_codex_config_three_keys_and_whole_file_hash(self):
        m = self.gen()
        self.assertEqual(m["codex"]["config"], {"model": "gpt-x",
                                                "model_reasoning_effort": "high",
                                                "service_tier": "fast"})
        self.assertEqual(m["codex"]["config_sha256"], freeze_common.sha256_file(
            os.path.join(self.fx.codex_home, "config.toml")))
        self.assertEqual(m["codex"]["cli_version"], "1.2.3")
        self.assertTrue(m["codex"]["project_codex_dir_absent"])
        self.assertEqual(m["codex"]["companion"]["gitCommitSha"], "a" * 40)

    def test_user_level_env_projection(self):
        env = self.gen()["runners"]["b3"]["user_level"]["env"]
        self.assertEqual(set(env), set(fm.ENV_ALLOWLIST))
        self.assertEqual(env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "64000")
        self.assertIsNone(env["ANTHROPIC_MODEL"])

    def test_harness_launch_model_and_env(self):
        h = self.gen(env={"ANTHROPIC_MODEL": "claude-x[1m]"})["runners"]["fix-harness"]
        self.assertEqual(h["launch_model"], {"value": "claude-fixture-1[1m]",
                                             "source": "probe-record"})
        self.assertEqual(h["env"]["ANTHROPIC_MODEL"], "claude-x[1m]")
        self.assertIsNone(h["env"]["ANTHROPIC_BASE_URL"])
        self.assertEqual(h["sdk_version"], "0.2.165")
        self.assertEqual(h["sdk_requirements_pin"], "0.2.165")
        self.assertEqual(h["bundled_cli"]["version"], "2.1.294")
        self.assertEqual(h["probe_settings_fingerprint"], "ab" * 32)
        self.assertEqual(h["setting_sources"], [])

    def test_harness_launch_model_missing_refused(self):
        _write(self.fx.repo, fm.HARNESS_PROBE, json.dumps({"passed": True}))
        _run(self.fx.repo, "git", "commit", "-qam", "c3")
        with self.assertRaises(FreezeError):
            self.gen()

    def test_every_allowlisted_env_key_generates(self):
        env = {k: "1" for k in fm.ENV_ALLOWLIST}
        env.update({k: "claude-opus-5-5[1m]" for k in fm.ENV_ALLOWLIST
                    if k.endswith("_MODEL")})
        env.update({"ANTHROPIC_BASE_URL": "https://gateway.example:8443/v1",
                    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000",
                    "CLAUDE_CODE_EFFORT_LEVEL": "high",
                    "VIBE_CHECK_TOP_MODEL": "fable"})
        m = self.gen(env=env)
        self.assertEqual(m["runners"]["fix-harness"]["env"], env)

    def test_credential_in_allowlisted_value_refused(self):
        for env in ({"ANTHROPIC_MODEL": "sk-ant-planted"},
                    {"ANTHROPIC_BASE_URL": "https://h/?token=ghp_x"},
                    {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": HOOK_UNPREFIXED}):
            with self.assertRaises(FreezeError) as cm:
                self.gen(env=env)
            key = next(iter(env))
            self.assertIn("runners.fix-harness.env." + key, str(cm.exception))
            self.assertNotIn(env[key], str(cm.exception))

    def test_permissions_hash(self):
        m = self.gen()
        perms = m["runners"]["b3"]["user_level"]["permissions"]
        self.assertRegex(perms, HEX64)
        self.assertEqual(perms, freeze_common.canonical_sha256(
            self.fx.settings()["permissions"]))
        joined = "\n".join(_strings(m))
        self.assertNotIn("git status", joined)
        self.assertNotIn("/tmp/x", joined)
        s = self.fx.settings()
        s["permissions"]["allow"].append("Bash(ls)")
        self.fx.write_settings(s)
        self.assertNotEqual(self.gen()["runners"]["b3"]["user_level"]["permissions"],
                            perms)
        del s["permissions"]
        self.fx.write_settings(s)
        self.assertIsNone(self.gen()["runners"]["b3"]["user_level"]["permissions"])

    def test_planted_secret_never_in_manifest(self):
        m = self.gen(env={"ANTHROPIC_API_KEY": PLANTED_KEY})
        for s in _strings(m):
            self.assertNotIn(PLANTED_KEY, s)
            self.assertNotIn("ANTHROPIC_API_KEY", s)

    def test_cosmetic_keys_not_projected(self):
        user = self.gen()["runners"]["b3"]["user_level"]
        for key in fm.COSMETIC_KEYS:
            self.assertNotIn(key, user)
        s = self.fx.settings()
        s["theme"] = "light"
        first = self.gen()["runners"]["b3"]["user_level"]
        self.fx.write_settings(s)
        self.assertEqual(self.gen()["runners"]["b3"]["user_level"], first)

    def test_user_level_fields(self):
        u = self.gen()["runners"]["b3"]["user_level"]
        self.assertEqual(u["claude_md_sha256"], freeze_common.sha256_file(
            os.path.join(self.fx.home, ".claude/CLAUDE.md")))
        self.assertEqual(set(u["enabled_plugins"]), {"p@m"})
        self.assertRegex(u["enabled_plugins"]["p@m"]["tree_sha256"], HEX64)
        self.assertEqual(u["effortLevel"], "xhigh")
        self.assertEqual(u["modelSettings"]["effort"], {"claude-fable-5-1": "medium"})
        self.assertIs(u["alwaysThinkingEnabled"], False)

    def test_malformed_enabled_plugins_is_a_freeze_error(self):
        """A non-object enabledPlugins stops generation with a named
        FreezeError (never a traceback from .items())."""
        for bad in (["p@m"], "p@m", 3, True):
            with self.subTest(bad=bad):
                s = self.fx.settings()
                s["enabledPlugins"] = bad
                self.fx.write_settings(s)
                with self.assertRaises(fm.FreezeError) as cm:
                    fm.user_level(self.fx.home, self.fx.repo)
                self.assertIn("enabledPlugins is not a JSON object", str(cm.exception))
        s = self.fx.settings()
        s["enabledPlugins"] = None
        self.fx.write_settings(s)
        self.assertEqual(fm.user_level(self.fx.home, self.fx.repo)[0]["enabled_plugins"], {})

    def test_limitations_and_manifest_id_stable(self):
        a, b = self.gen(), self.gen()
        self.assertTrue(a["limitations"])
        self.assertRegex(a["manifest_id"], HEX64)
        self.assertEqual(a["manifest_id"], b["manifest_id"])
        self.assertEqual(a["manifest_id"], fm.manifest_id(a))

    def test_freeze_manifest_file_not_covered(self):
        m = self.gen()
        for key, entry in m["covered"].items():
            for rel in entry["files"]:
                self.assertNotRegex(rel, r"FREEZE-MANIFEST-")
        self.assertEqual(m["covered"]["docs/design/freeze-v2.12/PATH-MAP.json"]
                         ["files"].keys(), {"PATH-MAP.json"})

    def test_covered_answer_keys(self):
        cov = self.gen()["covered"]
        self.assertIn("ANSWER-KEY-v2.10.md",
                      cov["docs/design/b3-ground-truth/ANSWER-KEY-*.md"]["files"])
        self.assertIn("probe/sandbox-probe.json",
                      cov["docs/design/fix-harness/fixtures"]["files"])

    def test_runner_settings(self):
        rs = self.gen()["runners"]["b3"]["runner_settings"]
        self.assertEqual(rs["template_path"], fm.RUNNER_TEMPLATE)
        self.assertEqual(rs["template_canonical_sha256"],
                         freeze_common.canonical_sha256(self.fx.template))
        self.assertEqual(rs["statusline_script_sha256"],
                         freeze_common.sha256_bytes(b"#!/bin/sh\ncat\n"))
        self.assertEqual(rs["substitution"],
                         {"key": "statusLine.command", "placeholder": "<RUNNER>"})
        self.assertEqual(self.gen()["runners"]["holdout-eval"]["runner_settings"], rs)

    def test_runner_settings_missing_template_refused_unless_allowed(self):
        with self.assertRaises(FreezeError):
            self.gen(candidate="HEAD~1")
        m = self.gen(candidate="HEAD~1", require_runner_settings=False)
        self.assertIsNone(m["runners"]["b3"]["runner_settings"])

    def test_runner_profiles(self):
        r = self.gen()["runners"]
        self.assertEqual(r["b3"]["cli"]["version"], "9.9.9")
        self.assertEqual(r["b3"]["context_window_expected"], 1000000)
        self.assertEqual(r["b3"]["gateway"]["version_id"], "0.51.2")
        self.assertEqual(r["b3"]["gateway"]["base_url"], "http://127.0.0.1:18764")
        self.assertFalse(r["holdout-autopilot"]["loads_plugin"])
        self.assertEqual(r["holdout-eval"]["user_level"], r["b3"]["user_level"])
        self.assertEqual(r["holdout-eval"]["contract"], list(fm.HOLDOUT_EVAL_CONTRACT))

    def test_lineage_null_for_first(self):
        self.assertEqual(self.gen()["lineage"], {"previous_manifest_id": None,
                                                 "previous_candidate_sha": None})

    def test_lineage_from_previous(self):
        first = self.gen(candidate="HEAD~1", require_runner_settings=False)
        path = os.path.join(self.fx.home, "prev.json")
        fm.write_manifest(path, first)
        m = self.gen(previous=path)
        self.assertEqual(m["lineage"]["previous_manifest_id"], first["manifest_id"])
        self.assertEqual(m["lineage"]["previous_candidate_sha"], first["candidate_sha"])
        first["candidate_sha"] = "0" * 40
        bad = os.path.join(self.fx.home, "bad.json")
        fm.write_manifest(bad, first)
        with self.assertRaises(FreezeError):
            self.gen(previous=bad)

    def test_runtime_fingerprint_matches_score43(self):
        scripts = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(HERE)))), "plugins", "vibe-check", "scripts")
        sys.path.insert(0, scripts)
        try:
            import score43
        finally:
            sys.path.remove(scripts)
        self.assertEqual(fm.RUNTIME_ROOTS, score43.RUNTIME_ROOTS)
        m = self.gen()
        self.assertEqual(m["plugin"]["runtime_fingerprint"], score43.runtime_fingerprint(
            os.path.join(self.fx.repo, "plugins", "vibe-check")))

    def test_home_none_resolves_to_real_home(self):
        env = dict(os.environ)
        env.pop("CODEX_HOME", None)
        env["HOME"] = self.fx.home
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(freeze_common.resolve_homes(None, None),
                             (self.fx.home, os.path.join(self.fx.home, ".codex")))
            self.assertEqual(freeze_common.resolve_homes("/x", None),
                             ("/x", "/x/.codex"))
            self.assertTrue(_home_none_equal(self.fx))


def _home_none_equal(fx):
    """True when generate(home=None) projects the same user level as an
    explicit home (caller sets HOME to the fixture home)."""
    try:
        a = fx.generate(home=None, codex_home=None)
    except Exception:
        return False
    b = fx.generate()
    ua = a["runners"]["b3"]["user_level"]
    return (ua == b["runners"]["b3"]["user_level"]
            and a["codex"]["config"] == b["codex"]["config"]
            and all(ua[k] is not None for k in ua))


# --------------------------------------------------------------------------- #
# Schema + secrets
# --------------------------------------------------------------------------- #

class TestSecrets(_Base):
    def setUp(self):
        super().setUp()
        self.m = self.gen()

    def _refused(self, m):
        with self.assertRaises(FreezeError) as cm:
            fm.assert_no_secrets(m)
        return str(cm.exception)

    def test_planted_credential_field_in_codex_refused(self):
        m = copy.deepcopy(self.m)
        m["codex"]["config"]["api_token"] = "example-plain-value"
        err = self._refused(m)
        self.assertIn("codex.config.api_token", err)
        self.assertNotIn("example-plain-value", err)

    def test_settingsmap_name_rule_refuses_a_listed_credential_field(self):
        node = fm.settingsmap({"api_token": fm.string(r"^[a-z-]+$")})
        problems = fm.validate_schema(node, {"api_token": "abc"}, "x")
        self.assertTrue(any("credential-named" in p for p in problems))

    def test_planted_unknown_key_refused(self):
        m = copy.deepcopy(self.m)
        m["runners"]["b3"]["extra"] = 1
        self.assertIn("runners.b3.extra", self._refused(m))

    def test_planted_credential_value_in_limitations_refused(self):
        m = copy.deepcopy(self.m)
        m["limitations"] = ["sk-ant-example-0000"]
        err = self._refused(m)
        self.assertIn("limitations[0]: credential-shaped value refused", err)
        self.assertNotIn("sk-ant-example-0000", err)

    def test_planted_private_key_block_refused(self):
        m = copy.deepcopy(self.m)
        m["limitations"] = ["-----BEGIN RSA PRIVATE KEY-----"]
        self.assertIn("limitations[0]: credential-shaped value refused",
                      self._refused(m))

    def test_hook_command_never_copied(self):
        m = self.m
        for s in _strings(m):
            self.assertNotIn(HOOK_GHP, s)
            self.assertNotIn(HOOK_UNPREFIXED, s)
        user = m["runners"]["b3"]["user_level"]
        self.assertRegex(user["hooks"], HEX64)
        self.assertEqual(list(user["hook_scripts"]), ["~/.claude/hooks/h.sh"])
        s = self.fx.settings()
        s["hooks"]["PreToolUse"][0]["hooks"][0]["command"] += " --more"
        self.fx.write_settings(s)
        self.assertNotEqual(self.gen()["runners"]["b3"]["user_level"]["hooks"],
                            user["hooks"])
        _write(self.fx.home, ".claude/hooks/h.sh", "#!/bin/sh\nexit 1\n")
        self.assertNotEqual(self.gen()["runners"]["b3"]["user_level"]["hook_scripts"],
                            user["hook_scripts"])

    def test_url_userinfo_refused(self):
        for value in ("https://runner:example-password@gateway.example/v1",
                      "https://runner@gateway.example/v1"):
            with self.assertRaises(FreezeError) as cm:
                self.gen(env={"ANTHROPIC_BASE_URL": value})
            err = str(cm.exception)
            self.assertIn("runners.fix-harness.env.ANTHROPIC_BASE_URL", err)
            self.assertNotIn("example-password", err)
            self.assertNotIn(value, err)

    def test_url_query_or_fragment_refused(self):
        for value in ("https://gateway.example/v1#frag",
                      "https://gateway.example/v1?x=1",
                      "https://gateway.example/v1?"):
            self.assertIsNotNone(fm.validate_url(value))
        self.assertIsNone(fm.validate_url("http://127.0.0.1:18764"))
        self.assertIsNone(fm.validate_url("https://gateway.example/v1"))
        self.assertIsNotNone(fm.validate_url("ftp://gateway.example/"))
        self.assertIsNotNone(fm.validate_url("https://"))

    def test_free_text_leaf_must_equal_constant(self):
        m = copy.deepcopy(self.m)
        m["limitations"] = ["an ordinary sentence about the run"]
        self.assertIn("limitations: must equal LIMITATIONS", self._refused(m))
        m["limitations"] = list(fm.LIMITATIONS)
        fm.assert_no_secrets(m)

    def test_no_free_text_node_in_schema(self):
        allowed = {"obj", "settingsmap", "pathmap", "coveredmap", "envmap", "strmap",
                   "identitymap", "hex40", "hex64", "hex64_or_null", "bool", "int",
                   "str", "url", "constlist", "list", "opt"}
        seen = set()

        def walk(node):
            seen.add(node.kind)
            self.assertIn(node.kind, allowed)
            if node.kind == "str":
                self.assertTrue(node.regex.startswith("^") and node.regex.endswith("$"))
                self.assertNotIn(".*", node.regex)
                self.assertNotIn(".+", node.regex)
            if node.kind in ("obj", "settingsmap"):
                for child in node.fields.values():
                    walk(child)
            if node.kind in ("pathmap", "coveredmap", "strmap"):
                walk(node.value)
            if node.kind in ("list", "opt"):
                walk(node.item)
            if node.kind == "identitymap":
                walk(fm.IDENTITY)
        walk(fm.MANIFEST_SCHEMA)
        self.assertIn("constlist", seen)

    def test_credential_word_in_path_key_accepted(self):
        files = self.m["plugin"]["files"]
        self.assertIn("scripts/token_counter.py", files)
        self.assertIn("agents/secret-handling.md", files)
        self.assertIn("docs/efficacy/ANSWER-KEY.md", files)
        fm.assert_no_secrets(self.m)

    def test_problems_never_echo_values(self):
        m = copy.deepcopy(self.m)
        m["plugin"]["plugin_json_version"] = "bad value with spaces"
        self.assertNotIn("bad value with spaces", self._refused(m))


@unittest.skipIf(REAL_REPO is None, "not inside a git checkout")
class TestRealTree(_Base):
    def test_real_tree_generation_succeeds(self):
        m = self.fx.generate(repo=REAL_REPO, require_runner_settings=False)
        fm.assert_no_secrets(m)
        self.assertTrue(any(k.endswith("ANSWER-KEY.md") for k in m["plugin"]["files"]))
        self.assertTrue(m["covered"]["docs/design/b3-ground-truth/ANSWER-KEY-*.md"]
                        ["files"])


# --------------------------------------------------------------------------- #
# write / verify-self / CLI
# --------------------------------------------------------------------------- #

class TestWriteVerify(_Base):
    def setUp(self):
        super().setUp()
        self.path = os.path.join(self.fx.home, "FREEZE-MANIFEST-1.json")
        fm.write_manifest(self.path, self.gen())

    def _load(self):
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def _rewrite(self, m):
        os.remove(self.path)
        fm.write_manifest(self.path, m)

    def test_write_refuses_existing_path(self):
        with self.assertRaises(FreezeError):
            fm.write_manifest(self.path, self._load())

    def test_verify_self_passes_fresh(self):
        self.assertEqual(fm.verify_self(self.fx.repo, self.path), [])

    def test_verify_self_tamper_plugin_hash_named(self):
        m = self._load()
        entry = m["plugin"]["files"]["scripts/x.py"]
        entry["sha256"] = ("0" if entry["sha256"][0] != "0" else "1") + entry["sha256"][1:]
        m["manifest_id"] = fm.manifest_id(m)
        self._rewrite(m)
        problems = fm.verify_self(self.fx.repo, self.path)
        self.assertIn("plugin file differs: scripts/x.py", problems)

    def test_verify_self_tamper_byte_fails(self):
        with open(self.path, encoding="utf-8") as fh:
            text = fh.read()
        sha = self._load()["plugin"]["files"]["agents/a.md"]["sha256"]
        flipped = ("f" if sha[-1] != "f" else "e")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(sha, sha[:-1] + flipped))
        problems = fm.verify_self(self.fx.repo, self.path)
        self.assertTrue(any("agents/a.md" in p for p in problems))
        self.assertIn("manifest_id does not match the manifest content", problems)

    def test_verify_self_tamper_manifest_id(self):
        m = self._load()
        m["manifest_id"] = "0" * 64
        self._rewrite(m)
        self.assertIn("manifest_id does not match the manifest content",
                      fm.verify_self(self.fx.repo, self.path))

    def _cli(self, *argv):
        env = dict(os.environ)
        env.update(self.fx.path_env())
        return subprocess.run([sys.executable, FM_PY, *argv], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=60, env=env)

    def test_cli_generate_show_verify_exit_codes(self):
        out = os.path.join(self.fx.home, "cli.json")
        gen = self._cli("generate", "--candidate", "HEAD", "--out", out,
                        "--repo", self.fx.repo, "--home", self.fx.home,
                        "--codex-home", self.fx.codex_home,
                        "--harness-venv", self.fx.venv)
        self.assertEqual(gen.returncode, 0, gen.stderr)
        show = self._cli("show", "--manifest", out)
        self.assertEqual(show.returncode, 0)
        self.assertIn(b"2.12.0", show.stdout)
        ok = self._cli("verify-self", "--manifest", out, "--repo", self.fx.repo)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        again = self._cli("generate", "--candidate", "HEAD", "--out", out,
                          "--repo", self.fx.repo, "--home", self.fx.home,
                          "--codex-home", self.fx.codex_home,
                          "--harness-venv", self.fx.venv)
        self.assertEqual(again.returncode, 1)
        m = json.load(open(out, encoding="utf-8"))
        m["manifest_id"] = "1" * 64
        os.remove(out)
        fm.write_manifest(out, m)
        bad = self._cli("verify-self", "--manifest", out, "--repo", self.fx.repo)
        self.assertEqual(bad.returncode, 1)

    def test_cli_usage_errors_exit_2(self):
        self.assertEqual(self._cli("bogus").returncode, 2)
        self.assertEqual(self._cli("generate", "--candidate", "HEAD").returncode, 2)
        self.assertEqual(self._cli().returncode, 2)


# --------------------------------------------------------------------------- #
# Import lock
# --------------------------------------------------------------------------- #

class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "hashlib", "json", "os", "re", "subprocess", "sys",
               "tomllib", "time", "datetime", "urllib.parse",
               "freeze_common", "freeze_policy"}

    def test_freeze_manifest_imports(self):
        with open(FM_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        self.assertTrue(names <= self.ALLOWED, names - self.ALLOWED)


# --------------------------------------------------------------------------- #
# Mutation matrix: each guard, removed, flips the test that proves it
# --------------------------------------------------------------------------- #

class TestMutants(_Base):
    def _ok(self, fn):
        try:
            fn()
            return True
        except (FreezeError, AssertionError):
            return False

    def test_mutant_worktree_reader_admits_untracked(self):
        _write(self.fx.repo, "plugins/vibe-check/agents/stray.md", "stray\n")
        self.assertNotIn("agents/stray.md", self.gen()["plugin"]["files"])
        real = freeze_common.tree_files_at

        def worktree(repo, rev, prefix, **kw):
            if prefix != fm.PLUGIN_ROOT:
                return real(repo, rev, prefix, **kw)
            return {rel: {"sha256": sha, "mode": "100644"} for rel, sha in
                    freeze_common.live_files(os.path.join(repo, prefix)).items()}
        with mock.patch.object(freeze_common, "tree_files_at", worktree):
            self.assertIn("agents/stray.md", self.gen()["plugin"]["files"])

    def test_mutant_m1_settingsmap_closed_set_removed(self):
        m = self.gen()
        m["codex"]["config"]["api_token"] = "example-plain-value"
        self.assertFalse(self._ok(lambda: fm.assert_no_secrets(m)))
        with mock.patch.object(fm, "_settingsmap_unknown", lambda *a: []):
            self.assertTrue(self._ok(lambda: fm.assert_no_secrets(m)))

    def test_mutant_m2_env_value_shapes_removed(self):
        env = {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": HOOK_UNPREFIXED}
        self.assertFalse(self._ok(lambda: self.gen(env=env)))
        with mock.patch.object(fm, "_env_value_problem", lambda *a: None):
            self.assertTrue(self._ok(lambda: self.gen(env=env)))

    def test_mutant_m3_key_substring_rule_reintroduced(self):
        real = fm.validate_schema

        def mutant(node, value, path=""):
            problems = real(node, value, path)
            if path == "":
                stack = [value]
                while stack:
                    v = stack.pop()
                    if isinstance(v, dict):
                        for k, x in v.items():
                            if re.search(r"(?i)key|token|secret", str(k)):
                                problems.append("credential word in key")
                            stack.append(x)
            return problems
        m = self.gen()
        self.assertTrue(self._ok(lambda: fm.assert_no_secrets(m)))
        with mock.patch.object(fm, "validate_schema", mutant):
            self.assertFalse(self._ok(lambda: fm.assert_no_secrets(m)))
            if REAL_REPO is not None:
                self.assertFalse(self._ok(lambda: self.fx.generate(
                    repo=REAL_REPO, require_runner_settings=False)))

    def test_mutant_m4_value_scan_removed(self):
        m = self.gen()
        m["limitations"] = ["sk-ant-example-0000"]

        def scan_hit():
            try:
                fm.assert_no_secrets(m)
            except FreezeError as exc:
                assert "credential-shaped value refused" in str(exc)
                return
            raise AssertionError("not refused")
        self.assertTrue(self._ok(scan_hit))
        with mock.patch.object(fm, "_scan_values", lambda *a: None):
            self.assertFalse(self._ok(scan_hit))

    def test_mutant_m5_validate_url_regex_only(self):
        env = {"ANTHROPIC_BASE_URL": "https://runner:example-password@gateway.example/v1"}
        self.assertFalse(self._ok(lambda: self.gen(env=env)))
        weak = lambda v: None if re.match(r"^https?://[^\s?#]+$", v or "") else "bad"  # noqa: E731
        with mock.patch.object(fm, "validate_url", weak):
            self.assertTrue(self._ok(lambda: self.gen(env=env)))

    def test_mutant_m6_hooks_object_copied(self):
        self.assertTrue(self._ok(self.gen))
        with mock.patch.object(fm, "_hooks_identity", lambda s: s.get("hooks")):
            self.assertFalse(self._ok(self.gen))

    def test_mutant_m7_constlist_equality_removed(self):
        m = self.gen()
        m["limitations"] = ["an ordinary sentence about the run"]
        self.assertFalse(self._ok(lambda: fm.assert_no_secrets(m)))
        with mock.patch.object(fm, "_constlist_problem", lambda *a: None):
            self.assertTrue(self._ok(lambda: fm.assert_no_secrets(m)))

    def test_mutant_m8_resolve_homes_passthrough(self):
        env = dict(os.environ)
        env.pop("CODEX_HOME", None)
        env["HOME"] = self.fx.home
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertTrue(_home_none_equal(self.fx))
            with mock.patch.object(freeze_common, "resolve_homes", lambda h, c: (h, c)):
                self.assertFalse(_home_none_equal(self.fx))

    def test_mutant_frontmatter_reads_body(self):
        self.assertEqual(self.gen()["models"]["agent_pins"], {"a": "opus"})

        def whole_text(text):
            found = None
            for line in text.splitlines():
                m = re.match(r"^model:\s*(\S+)", line)
                if m:
                    found = m.group(1)
            return found
        with mock.patch.object(fm, "_frontmatter_model", whole_text):
            self.assertIn("index", self.gen()["models"]["agent_pins"])

    def test_mutant_covered_exclusion_removed(self):
        files = self.gen()["covered"]["docs/design/freeze-v2.12/tools"]["files"]
        self.assertNotIn("FREEZE-MANIFEST-1.json", files)
        with mock.patch.object(fm, "_covered_excluded", lambda full: False):
            files = self.gen()["covered"]["docs/design/freeze-v2.12/tools"]["files"]
            self.assertIn("FREEZE-MANIFEST-1.json", files)


if __name__ == "__main__":
    unittest.main()
