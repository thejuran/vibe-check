"""Tests for harness_sandbox: the containment policy every harness session runs under.

Run with bare `pytest -q` from this directory. Every lock has a mutant test that
patches the lock out and asserts the outcome flips.
"""

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_fixture as hf  # noqa: E402
import harness_sandbox as h  # noqa: E402

COPY = "/private/tmp/w/repo"
SNAP = "/private/tmp/w/plugin"
CHECKOUT = "/Users/me/repo"
OUT = "/Users/me/repo/docs/design/fix-harness/runs/x"
KEYS = "/Users/me/repo/docs/design/fix-harness/keys"


def _sample_settings(copy_root=COPY, snapshot=SNAP, out=OUT):
    return h.build_session_settings(copy_root, snapshot, out, CHECKOUT, KEYS)


def _git(repo, *args):
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"})
    proc = subprocess.run(["git", "-C", repo, *args], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args, proc.stderr))
    return proc.stdout


class _TmpCase(unittest.TestCase):
    def mkdtemp(self):
        d = os.path.realpath(tempfile.mkdtemp(prefix="sandbox-test-"))
        self.addCleanup(shutil.rmtree, d, True)
        return d


class TestWorkspace(_TmpCase):
    def test_workspace_is_realpath_and_outside_checkout(self):
        ws = h.make_workspace()
        self.addCleanup(shutil.rmtree, ws, True)
        self.assertTrue(os.path.isdir(ws))
        self.assertEqual(ws, os.path.realpath(ws))
        self.assertFalse(h._is_under(ws, h.CHECKOUT_ROOT))

    def test_workspace_under_checkout_is_refused_and_removed(self):
        parent = self.mkdtemp()
        with mock.patch.object(h, "CHECKOUT_ROOT", parent), \
                mock.patch("tempfile.gettempdir", return_value=parent):
            with self.assertRaises(h.SandboxError):
                h.make_workspace()
        self.assertEqual(os.listdir(parent), [])

    def test_checkout_root_is_the_repo(self):
        self.assertTrue(os.path.isdir(os.path.join(h.CHECKOUT_ROOT, ".git")))
        self.assertTrue(os.path.isdir(os.path.join(h.CHECKOUT_ROOT,
                                                   "plugins", "vibe-check")))


class TestSnapshot(_TmpCase):
    def _fake_checkout(self):
        repo = self.mkdtemp()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "t")
        src = os.path.join(repo, "plugins", "vibe-check")
        os.makedirs(os.path.join(src, "scripts", "__pycache__"))
        os.makedirs(os.path.join(src, ".pytest_cache"))
        os.makedirs(os.path.join(src, ".venv"))
        with open(os.path.join(src, "scripts", "a.py"), "w") as fh:
            fh.write("A = 1\n")
        with open(os.path.join(src, "scripts", "a.pyc"), "w") as fh:
            fh.write("junk")
        with open(os.path.join(src, "scripts", "__pycache__", "x"), "w") as fh:
            fh.write("junk")
        with open(os.path.join(src, ".pytest_cache", "x"), "w") as fh:
            fh.write("junk")
        with open(os.path.join(src, ".venv", "x"), "w") as fh:
            fh.write("junk")
        with open(os.path.join(src, "README.md"), "w") as fh:
            fh.write("hello\n")
        with open(os.path.join(repo, ".gitignore"), "w") as fh:
            fh.write("__pycache__/\n*.pyc\n.pytest_cache/\n.venv/\n")
        _git(repo, "add", ".gitignore", "plugins/vibe-check/scripts/a.py",
             "plugins/vibe-check/README.md")
        _git(repo, "commit", "-q", "-m", "init")
        return repo, src

    def test_snapshot_copies_without_caches_and_records_provenance(self):
        repo, src = self._fake_checkout()
        dest = self.mkdtemp()
        snap = h.snapshot_plugin(src, dest, checkout_root=repo)
        self.assertEqual(snap.path, os.path.join(dest, "plugin"))
        files = sorted(os.path.relpath(os.path.join(r, f), snap.path)
                       for r, _d, fs in os.walk(snap.path) for f in fs)
        self.assertEqual(files, ["README.md", "scripts/a.py"])
        self.assertEqual(snap.git_sha, _git(repo, "rev-parse", "HEAD").strip())
        self.assertFalse(snap.dirty)
        self.assertEqual(snap.source_path, src)
        self.assertEqual(len(snap.tree_sha256), 64)

    def test_tree_hash_is_content_sensitive_and_dirty_is_recorded(self):
        repo, src = self._fake_checkout()
        a = h.snapshot_plugin(src, self.mkdtemp(), checkout_root=repo)
        b = h.snapshot_plugin(src, self.mkdtemp(), checkout_root=repo)
        self.assertEqual(a.tree_sha256, b.tree_sha256)
        with open(os.path.join(src, "README.md"), "a") as fh:
            fh.write("more\n")
        c = h.snapshot_plugin(src, self.mkdtemp(), checkout_root=repo)
        self.assertNotEqual(a.tree_sha256, c.tree_sha256)
        self.assertTrue(c.dirty)

    def test_snapshot_under_checkout_is_refused(self):
        repo, src = self._fake_checkout()
        with self.assertRaises(h.SandboxError):
            h.snapshot_plugin(src, os.path.join(repo, "inside"),
                              checkout_root=repo)
        self.assertFalse(os.path.exists(os.path.join(repo, "inside", "plugin")))


class TestSessionSettings(unittest.TestCase):
    def test_exact_policy_for_sample_paths(self):
        expected = {
            "sandbox": {
                "enabled": True,
                "failIfUnavailable": True,
                "allowUnsandboxedCommands": False,
                "autoAllowBashIfSandboxed": False,
                "excludedCommands": [],
                "filesystem": {
                    "denyRead": [CHECKOUT, OUT, KEYS,
                                 *h.PROTECTED_CREDENTIAL_PATHS],
                    "allowRead": [COPY, SNAP],
                    "denyWrite": [SNAP, COPY + "/probe.sh"],
                },
                "network": {"allowedDomains": [], "strictAllowlist": True},
            },
            "permissions": {
                "deny": [
                    "Read(//Users/me/repo/**)",
                    "Read(//Users/me/repo/docs/design/fix-harness/runs/x/**)",
                    "Read(//Users/me/repo/docs/design/fix-harness/keys/**)",
                    "Read(~/.ssh/**)", "Read(~/.aws/**)",
                    "Read(~/.config/gh/**)", "Read(~/.netrc)",
                    "Read(~/.gnupg/**)", "Read(~/.claude/.credentials.json)",
                    "Read(~/.claude.json)",
                    "Edit(//private/tmp/w/plugin/**)",
                    "Edit(//private/tmp/w/repo/probe.sh)",
                    "NotebookEdit",
                ],
                "defaultMode": "default",
            },
            "disableClaudeAiConnectors": True,
        }
        self.assertEqual(_sample_settings(), expected)
        self.assertTrue(h.settings_is_fail_closed(_sample_settings()))

    def test_credential_paths(self):
        self.assertEqual(h.PROTECTED_CREDENTIAL_PATHS, (
            "~/.ssh", "~/.aws", "~/.config/gh", "~/.netrc", "~/.gnupg",
            "~/.claude/.credentials.json", "~/.claude.json"))

    def test_copy_or_snapshot_under_checkout_is_refused(self):
        with self.assertRaises(h.SandboxError):
            _sample_settings(copy_root=CHECKOUT + "/sub/repo")
        with self.assertRaises(h.SandboxError):
            _sample_settings(snapshot=CHECKOUT + "/plugin")

    def test_non_absolute_or_non_normal_paths_are_refused(self):
        with self.assertRaises(h.SandboxError):
            _sample_settings(copy_root="relative/repo")
        with self.assertRaises(h.SandboxError):
            _sample_settings(copy_root="/private/tmp/w/../w/repo")
        with self.assertRaises(h.SandboxError):
            _sample_settings(copy_root="/tmp/w/repo")  # /tmp is a symlink on macOS

    def test_fingerprint_stable_across_workspaces(self):
        a = _sample_settings()
        b = _sample_settings("/private/tmp/v/repo", "/private/tmp/v/plugin",
                             "/Users/me/repo/docs/design/fix-harness/runs/y")
        self.assertEqual(h.settings_fingerprint(a), h.settings_fingerprint(b))
        self.assertEqual(len(h.settings_fingerprint(a)), 64)

    def test_fingerprint_changes_with_policy(self):
        a = _sample_settings()
        b = copy.deepcopy(a)
        b["sandbox"]["network"]["strictAllowlist"] = False
        self.assertNotEqual(h.settings_fingerprint(a), h.settings_fingerprint(b))
        c = copy.deepcopy(a)
        c["permissions"]["deny"].remove("NotebookEdit")
        self.assertNotEqual(h.settings_fingerprint(a), h.settings_fingerprint(c))

    def test_fail_closed_rejects_each_weakening(self):
        weakenings = [
            lambda s: s["sandbox"].update(enabled=False),
            lambda s: s["sandbox"]["filesystem"]["denyRead"].remove(KEYS),
            lambda s: s["sandbox"]["filesystem"]["denyWrite"].clear(),
            lambda s: s["permissions"]["deny"].remove(
                "Read(//Users/me/repo/docs/design/fix-harness/keys/**)"),
            lambda s: s["permissions"]["deny"].remove(
                "Edit(//private/tmp/w/plugin/**)"),
            lambda s: s["permissions"]["deny"].remove("NotebookEdit"),
            lambda s: s["permissions"]["deny"].remove("Read(~/.ssh/**)"),
            lambda s: s["sandbox"]["filesystem"]["denyRead"].remove("~/.aws"),
            lambda s: s["sandbox"].update(excludedCommands=["git"]),
            lambda s: s["sandbox"]["filesystem"]["denyWrite"].remove(
                COPY + "/probe.sh"),
            lambda s: s["permissions"]["deny"].remove(
                "Edit(//private/tmp/w/repo/probe.sh)"),
            lambda s: s.pop("disableClaudeAiConnectors"),
            lambda s: s.update(disableClaudeAiConnectors=False),
        ]
        for weaken in weakenings:
            s = _sample_settings()
            weaken(s)
            self.assertFalse(h.settings_is_fail_closed(s))
        self.assertFalse(h.settings_is_fail_closed({}))
        self.assertFalse(h.settings_is_fail_closed(None))

    # Mutants: a patched builder that weakens one lock must flip the predicate.

    def _mutant(self, mutate):
        real = h.build_session_settings

        def patched(*a, **k):
            s = real(*a, **k)
            mutate(s)
            return s
        with mock.patch.object(h, "build_session_settings", patched):
            return h.build_session_settings(COPY, SNAP, OUT, CHECKOUT, KEYS)

    def test_m14_connectors_left_enabled_flips(self):
        self.assertTrue(h.settings_is_fail_closed(_sample_settings()))
        s = self._mutant(lambda s: s.pop("disableClaudeAiConnectors"))
        self.assertFalse(h.settings_is_fail_closed(s))

    def test_m1_dropping_fail_if_unavailable_flips(self):
        self.assertTrue(h.settings_is_fail_closed(_sample_settings()))
        s = self._mutant(lambda s: s["sandbox"].pop("failIfUnavailable"))
        self.assertFalse(h.settings_is_fail_closed(s))

    def test_m2_allowing_unsandboxed_commands_flips(self):
        s = self._mutant(
            lambda s: s["sandbox"].update(allowUnsandboxedCommands=True))
        self.assertFalse(h.settings_is_fail_closed(s))

    def test_m3_missing_checkout_read_deny_flips(self):
        s = self._mutant(
            lambda s: s["permissions"]["deny"].remove("Read(//Users/me/repo/**)"))
        self.assertFalse(h.settings_is_fail_closed(s))


class TestPathBackstop(_TmpCase):
    def setUp(self):
        self.ws = self.mkdtemp()
        self.copy = os.path.join(self.ws, "repo")
        self.snap = os.path.join(self.ws, "plugin")
        self.outside = self.mkdtemp()
        self.out = self.mkdtemp()
        os.makedirs(os.path.join(self.copy, "nested"))
        os.makedirs(os.path.join(self.snap, "scripts"))
        with open(os.path.join(self.copy, "inside.txt"), "w") as fh:
            fh.write("x")
        os.symlink(self.outside, os.path.join(self.copy, "link_out"))
        self.roots = h.protected_roots(self.out)

    def check(self, tool, data):
        return h.path_allowed(tool, data, self.copy, self.snap, self.roots)

    def test_read_inside_copy_ok_relative_and_absolute(self):
        r = self.check("Read", {"file_path": "inside.txt"})
        self.assertEqual(r, h.Decision(True, "copy",
                                       os.path.join(self.copy, "inside.txt")))
        r = self.check("Write", {"file_path": self.copy + "/new.txt",
                                 "content": "x"})
        self.assertEqual((r.ok, r.kind), (True, "copy"))

    # MCP tools run inside the Claude Code process, outside Seatbelt and
    # outside the copy; the smoke session reached the owner's account
    # connectors through one. Every `mcp__` tool is external, path or not.
    def test_mcp_tools_are_external(self):
        for tool, data in (
                ("mcp__claude_ai_Claude_Docs__update",
                 {"payload": {"note": "x"},
                  "ref": {"id": "src/clamp.py", "object": "file"}}),
                ("mcp__claude_ai_Gmail__send", {}),
                ("mcp__srv__read", {"file_path": self.copy + "/inside.txt"})):
            r = self.check(tool, data)
            self.assertEqual((r.ok, r.kind), (False, "external"), tool)

    def test_m15_mcp_rule_is_load_bearing(self):
        data = {"payload": {}, "ref": {"id": "x", "object": "file"}}
        self.assertFalse(self.check("mcp__claude_ai_Gmail__send", data).ok)
        with mock.patch.object(h, "_is_external_tool", lambda name: False):
            self.assertTrue(self.check("mcp__claude_ai_Gmail__send", data).ok)

    def test_builtin_pathless_tools_stay_allowed(self):
        for tool in ("Bash", "Agent", "TodoWrite", "ToolSearch", "Skill"):
            self.assertTrue(self.check(tool, {"command": "x"}).ok, tool)

    def test_symlink_escape_is_outside(self):
        r = self.check("Edit", {"file_path": self.copy + "/link_out/x",
                                "old_string": "a", "new_string": "b"})
        self.assertEqual((r.ok, r.kind), (False, "outside"))
        self.assertEqual(r.path, self.copy + "/link_out/x")

    def test_dotdot_traversal_is_outside(self):
        r = self.check("Read", {"file_path": "../other"})
        self.assertEqual((r.ok, r.kind), (False, "outside"))
        r = self.check("Read", {"file_path": "nested/../../elsewhere/x"})
        self.assertEqual((r.ok, r.kind), (False, "outside"))
        r = self.check("Edit", {"file_path": "nested/../../plugin/x",
                                "old_string": "a", "new_string": "b"})
        self.assertEqual((r.ok, r.kind), (False, "snapshot"))

    def test_keys_and_checkout_and_out_are_protected(self):
        for path in (os.path.join(str(hf.KEYS_DIR), "py-clamp-01.json"),
                     os.path.join(h.CHECKOUT_ROOT, "README.md"),
                     os.path.join(self.out, "protected", "canary.txt"),
                     os.path.expanduser("~/.ssh/id_rsa"),
                     os.path.expanduser("~/.claude.json")):
            r = self.check("Read", {"file_path": path})
            self.assertEqual((r.ok, r.kind), (False, "protected"), path)

    def test_symlink_into_protected_root_is_protected(self):
        os.symlink(self.out, os.path.join(self.copy, "link_prot"))
        r = self.check("Read", {"file_path": "link_prot/canary.txt"})
        self.assertEqual((r.ok, r.kind), (False, "protected"))

    def test_symlink_out_of_protected_root_is_still_protected(self):
        os.symlink(self.outside, os.path.join(self.out, "esc"))
        r = self.check("Read", {"file_path": self.out + "/esc/x"})
        self.assertEqual((r.ok, r.kind), (False, "protected"))

    def test_snapshot_is_read_only(self):
        target = self.snap + "/scripts/gitguard.py"
        for tool, data in (("Read", {"file_path": target}),
                           ("Grep", {"pattern": "x", "path": self.snap}),
                           ("Glob", {"pattern": "*.py", "path": self.snap})):
            r = self.check(tool, data)
            self.assertEqual((r.ok, r.kind), (True, "snapshot"), tool)
        for tool, data in (("Edit", {"file_path": target, "old_string": "a",
                                     "new_string": "b"}),
                           ("Write", {"file_path": target, "content": "x"}),
                           ("NotebookEdit", {"notebook_path": target})):
            self.assertFalse(self.check(tool, data).ok, tool)

    def test_tools_without_a_path(self):
        self.assertEqual(self.check("Bash", {"command": "cat /etc/hosts"}),
                         h.Decision(True, "no-path", None))
        self.assertEqual(self.check("AskUserQuestion", {"questions": []}),
                         h.Decision(True, "no-path", None))

    def test_grep_glob_default_to_copy(self):
        r = self.check("Grep", {"pattern": "x"})
        self.assertEqual(r, h.Decision(True, "copy", self.copy))
        r = self.check("Glob", {"pattern": "**/*.py"})
        self.assertEqual(r, h.Decision(True, "copy", self.copy))

    def test_glob_pattern_cannot_escape(self):
        r = self.check("Glob", {"pattern": self.outside + "/**/*"})
        self.assertFalse(r.ok)
        r = self.check("Glob", {"pattern": "../**/*.json"})
        self.assertFalse(r.ok)
        r = self.check("Glob", {"pattern": "~/.ssh/*"})
        self.assertFalse(r.ok)

    def test_tilde_path_is_expanded(self):
        r = self.check("Read", {"file_path": "~/.aws/credentials"})
        self.assertEqual((r.ok, r.kind), (False, "protected"))

    def test_unknown_tool_with_path_field_is_bounded(self):
        r = self.check("SomeNewTool", {"file_path": self.outside + "/x"})
        self.assertFalse(r.ok)

    def test_malformed_path_is_denied(self):
        self.assertFalse(self.check("Read", {"file_path": 42}).ok)
        self.assertFalse(self.check("Read", {}).ok)

    def test_m4_identity_realpath_lets_symlink_escape(self):
        with mock.patch("os.path.realpath", lambda p: p):
            r = self.check("Edit", {"file_path": self.copy + "/link_out/x",
                                    "old_string": "a", "new_string": "b"})
        self.assertTrue(r.ok)


class TestPreflight(_TmpCase):
    SDK = "0.2.165"

    def setUp(self):
        ws = self.mkdtemp()
        self.copy = os.path.join(ws, "repo")
        self.snap = os.path.join(ws, "plugin")
        os.makedirs(self.copy)
        os.makedirs(self.snap)
        self.out = self.mkdtemp()
        self.settings = h.build_session_settings(self.copy, self.snap, self.out)
        self.record_path = os.path.join(self.mkdtemp(), "sandbox-probe.json")
        self.write_record()

    def write_record(self, **over):
        record = {"passed": True, "sdk_version": self.SDK,
                  "settings_fingerprint": h.settings_fingerprint(self.settings),
                  "checks": {k: True for k in h.PROBE_REQUIRED_CHECKS}}
        record.update(over)
        with open(self.record_path, "w") as fh:
            json.dump(record, fh)

    def run_preflight(self, settings=None):
        return h.preflight(self.copy, self.snap, settings or self.settings,
                           self.record_path, self.SDK)

    def assert_probe_problem(self, problems):
        self.assertIn(h.PROBE_STALE_PROBLEM, problems)

    def test_all_good(self):
        self.assertEqual(self.run_preflight(), [])

    def test_missing_probe(self):
        os.remove(self.record_path)
        self.assert_probe_problem(self.run_preflight())

    def test_garbled_probe(self):
        with open(self.record_path, "w") as fh:
            fh.write("{not json")
        self.assert_probe_problem(self.run_preflight())

    def test_failed_probe(self):
        self.write_record(passed=False)
        self.assert_probe_problem(self.run_preflight())

    def test_truthy_but_not_true_passed(self):
        self.write_record(passed="yes")
        self.assert_probe_problem(self.run_preflight())

    def test_stale_sdk_version(self):
        self.write_record(sdk_version="0.2.164")
        self.assert_probe_problem(self.run_preflight())

    def test_stale_fingerprint(self):
        self.write_record(settings_fingerprint="0" * 64)
        self.assert_probe_problem(self.run_preflight())

    def test_a_false_check(self):
        checks = {k: True for k in h.PROBE_REQUIRED_CHECKS}
        checks["extra_check"] = False
        self.write_record(checks=checks)
        self.assert_probe_problem(self.run_preflight())

    def test_weakened_settings(self):
        weak = copy.deepcopy(self.settings)
        weak["sandbox"]["failIfUnavailable"] = False
        problems = self.run_preflight(weak)
        self.assertTrue(problems)

    def test_settings_for_another_copy(self):
        other = h.build_session_settings(self.mkdtemp(), self.snap, self.out)
        self.assertTrue(self.run_preflight(other))

    def test_copy_under_checkout(self):
        problems = h.preflight(h.CHECKOUT_ROOT + "/x", self.snap,
                               self.settings, self.record_path, self.SDK)
        self.assertTrue(any("inside the checkout" in p for p in problems),
                        problems)

    def test_unsupported_host(self):
        with mock.patch.object(h.sys, "platform", "linux"):
            self.assertIn(h.UNSUPPORTED_HOST_PROBLEM, self.run_preflight())

    def test_seatbelt_missing(self):
        real = os.access

        def access(path, mode):
            if path == "/usr/bin/sandbox-exec":
                return False
            return real(path, mode)
        with mock.patch("os.access", access):
            self.assertTrue(self.run_preflight())

    def test_record_missing_a_tool_denial_check_is_stale(self):
        checks = {k: True for k in h.PROBE_REQUIRED_CHECKS}
        checks.pop("read_key_tool_denied")
        self.write_record(checks=checks)
        self.assert_probe_problem(self.run_preflight())

    def test_record_missing_preconditions_check_is_stale(self):
        checks = {k: True for k in h.PROBE_REQUIRED_CHECKS}
        checks.pop("preconditions_hold")
        self.write_record(checks=checks)
        self.assert_probe_problem(self.run_preflight())

    def test_m5_skipping_fingerprint_comparison_accepts_stale_record(self):
        self.write_record(settings_fingerprint="0" * 64)
        self.assertTrue(self.run_preflight())
        with mock.patch.object(h, "_fingerprint_matches", lambda r, s: True):
            self.assertEqual(self.run_preflight(), [])


# ---------------------------------------------------------------------------
# Sandbox probe
# ---------------------------------------------------------------------------

NONCE = "abc123"
PP = {"PROTECTED": "/private/tmp/o/protected",
      "KEYS_DIR": "/Users/me/repo/docs/design/fix-harness/keys",
      "SNAPSHOT": "/private/tmp/w/plugin", "COPY": "/private/tmp/w/repo",
      "NONCE": NONCE}
SCRIPT_PATHS = {"PROTECTED": PP["PROTECTED"], "KEYS_DIR": PP["KEYS_DIR"],
                "CHECKOUT": "/Users/me/repo", "SNAPSHOT": PP["SNAPSHOT"],
                "NONCE": NONCE}
PROT_CANARY = "HARNESS-PROTECTED-0123456789abcdef"
COPY_CANARY = "HARNESS-COPY-fedcba9876543210"
KEY_TITLE = "clamp keeps values one below the upper bound"
BASH_STEPS = [st for st in h.PROBE_STEPS if st[1] == "bash"]
TOOL_STEPS = [st for st in h.PROBE_STEPS if st[1] != "bash"]
BASH_DENY_TEXT = {
    "read_protected_bash": "cat: %s/canary.txt: Operation not permitted"
                           % PP["PROTECTED"],
    "read_key_bash": "cat: %s/py-clamp-01.json: Operation not permitted"
                     % PP["KEYS_DIR"],
    "write_checkout_bash": "touch: /Users/me/repo/HARNESS-ESCAPE-%s: "
                           "Operation not permitted" % NONCE,
    "write_snapshot_bash": "touch: %s/HARNESS-ESCAPE-%s: Operation not "
                           "permitted" % (PP["SNAPSHOT"], NONCE),
}


SCRIPT_SHA = "c" * 64


def _facts(**over):
    facts = {"copy_root": PP["COPY"], "protected_canary": PROT_CANARY,
             "copy_canary": COPY_CANARY, "key_title": KEY_TITLE,
             "expected_inputs": h.PROBE_TOOL_INPUTS(**PP),
             "protected_canary_exists": True, "key_file_exists": True,
             "protected_dir_exists": True, "edit_target_exists": True,
             "edit_target_intact": True, "escape_file_exists": False,
             "snapshot_escape_exists": False, "protected_escape_exists": False,
             "snapshot_sha_before": "a" * 64, "snapshot_sha_after": "a" * 64,
             "copy_marker_exists": True, "copy_tool_marker_exists": True,
             "probe_script_expected_sha": SCRIPT_SHA,
             "probe_script_sha_before": SCRIPT_SHA,
             "probe_script_sha_after": SCRIPT_SHA}
    facts.update(over)
    return facts


def _ev(tool, inp, is_error, text, decision=None):
    path = inp.get("file_path") if isinstance(inp, dict) else None
    return h.ProbeEvent(tool, os.path.normpath(os.path.join(PP["COPY"], path))
                        if path else None, inp, inp.get("command"), decision,
                        is_error, text)


def _markers(over=None, only=None):
    over = over or {}
    lines = []
    for n, (name, _ch, expect) in enumerate(BASH_STEPS, 1):
        if only is not None and name not in only:
            continue
        if name in over:
            tail = over[name]
        elif expect == "deny":
            tail = "exit=1 err=" + BASH_DENY_TEXT[name]
        elif name == "read_copy_bash":
            tail = "exit=0 err=" + COPY_CANARY
        else:
            tail = "exit=0 err="
        lines.append("PROBE-STEP %d %s %s" % (n, name, tail))
    lines.append("PROBE-SCRIPT-END")
    return "\n".join(lines) + "\n"


def _script_event(text):
    return _ev("Bash", {"command": "bash ./probe.sh",
                        "description": "run the probe"}, False, text, "allow")


def _tool_event(name, facts, **over):
    step = dict((st[0], st) for st in TOOL_STEPS)[name]
    inp = dict(facts["expected_inputs"][name])
    if step[2] == "deny":
        is_error = True
        text = "Permission to use %s has been denied." % step[1]
    else:
        is_error = False
        text = ("1\t" + COPY_CANARY) if name == "read_copy_tool" else \
            "File created successfully"
    inp.update(over.pop("input_update", {}))
    for key in over.pop("input_drop", ()):
        inp.pop(key)
    ev = _ev(step[1], inp, is_error, text)
    return ev._replace(**over)


def _happy_events(facts, markers=None, tool_over=None):
    tool_over = tool_over or {}
    events = [_script_event(markers if markers is not None else _markers())]
    for name, _ch, _ex in TOOL_STEPS:
        events.append(_tool_event(name, facts, **tool_over.get(name, {})))
    return events


def _failed(checks):
    return sorted(k for k, v in checks.items() if v is not True)


class TestProbeScript(_TmpCase):
    def test_steps_and_required_checks(self):
        self.assertEqual([st[0] for st in BASH_STEPS], [
            "read_protected_bash", "read_key_bash", "write_checkout_bash",
            "write_snapshot_bash", "read_copy_bash", "write_copy_bash"])
        self.assertEqual([(st[0], st[1], st[2]) for st in TOOL_STEPS], [
            ("read_protected_tool", "Read", "deny"),
            ("read_key_tool", "Read", "deny"),
            ("write_protected_tool", "Write", "deny"),
            ("edit_snapshot_tool", "Edit", "deny"),
            ("read_copy_tool", "Read", "allow"),
            ("write_copy_tool", "Write", "allow")])
        req = set(h.PROBE_REQUIRED_CHECKS)
        self.assertEqual(len(req), len(h.PROBE_REQUIRED_CHECKS))
        for name, _ch, expect in h.PROBE_STEPS:
            self.assertIn(name + "_attempted", req)
            self.assertIn(name + ("_denied" if expect == "deny" else "_ok"),
                          req)

    def test_tool_inputs_are_complete_and_exact(self):
        ti = h.PROBE_TOOL_INPUTS(**PP)
        self.assertEqual(ti, {
            "read_protected_tool": {"file_path": PP["PROTECTED"] +
                                    "/canary.txt"},
            "read_key_tool": {"file_path": PP["KEYS_DIR"] +
                              "/py-clamp-01.json"},
            "write_protected_tool": {"file_path": PP["PROTECTED"] +
                                     "/escape.txt",
                                     "content": "HARNESS-ESCAPE-" + NONCE},
            "edit_snapshot_tool": {"file_path": PP["SNAPSHOT"] +
                                   "/PROBE-EDIT-TARGET.txt",
                                   "old_string": "HARNESS-EDIT-TARGET-" + NONCE,
                                   "new_string": "HARNESS-EDIT-DONE-" + NONCE},
            "read_copy_tool": {"file_path": PP["COPY"] + "/PROBE.txt"},
            "write_copy_tool": {"file_path": PP["COPY"] + "/tool-ok.txt",
                                "content": "HARNESS-TOOL-OK"},
        })

    def test_script_is_deterministic_and_marked(self):
        a = h.fill_probe_script(**SCRIPT_PATHS)
        self.assertEqual(a, h.fill_probe_script(**SCRIPT_PATHS))
        self.assertTrue(a.startswith("#!/bin/bash\n"))
        self.assertIn("set +e", a)
        self.assertIn("mkdir -p probe-tmp", a)
        self.assertEqual(a.count("PROBE-STEP"), 6)
        last = -1
        for n, (name, _ch, _ex) in enumerate(BASH_STEPS, 1):
            marker = "PROBE-STEP %d %s exit=" % (n, name)
            self.assertIn(marker, a)
            self.assertGreater(a.index(marker), last)
            last = a.index(marker)
            self.assertIn("> probe-tmp/step%d.out 2>&1" % n, a)
            self.assertIn("head -c 200 probe-tmp/step%d.out" % n, a)
        self.assertTrue(a.rstrip().endswith('echo "PROBE-SCRIPT-END"'))
        self.assertIn("/Users/me/repo/HARNESS-ESCAPE-" + NONCE, a)
        self.assertIn(PP["SNAPSHOT"] + "/HARNESS-ESCAPE-" + NONCE, a)

    def test_script_quotes_paths(self):
        paths = dict(SCRIPT_PATHS, PROTECTED="/tmp/a b/$(touch pwned)")
        s = h.fill_probe_script(**paths)
        self.assertIn("'/tmp/a b/$(touch pwned)/canary.txt'", s)

    def test_script_passes_bash_syntax_check(self):
        d = self.mkdtemp()
        path = os.path.join(d, "probe.sh")
        with open(path, "w") as fh:
            fh.write(h.fill_probe_script(**SCRIPT_PATHS))
        proc = subprocess.run(["bash", "-n", path], capture_output=True,
                              text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    @unittest.skipUnless(os.path.exists("/bin/bash"), "needs /bin/bash")
    def test_live_markers_enoent_is_not_a_denial(self):
        root = self.mkdtemp()
        cwd = os.path.join(root, "copy")
        os.makedirs(cwd)
        with open(os.path.join(cwd, "PROBE.txt"), "w") as fh:
            fh.write(COPY_CANARY)
        gone = os.path.join(root, "missing")
        paths = {"PROTECTED": gone + "/protected", "KEYS_DIR": gone + "/keys",
                 "CHECKOUT": gone + "/checkout", "SNAPSHOT": gone + "/snap",
                 "NONCE": NONCE}
        with open(os.path.join(cwd, "probe.sh"), "w") as fh:
            fh.write(h.fill_probe_script(**paths))
        proc = subprocess.run(["/bin/bash", "./probe.sh"], cwd=cwd,
                              capture_output=True, text=True, timeout=60)
        out = proc.stdout
        self.assertIn("PROBE-SCRIPT-END", out)
        lines = {ln.split()[2]: ln for ln in out.splitlines()
                 if ln.startswith("PROBE-STEP ")}
        for name, _ch, expect in BASH_STEPS:
            if expect == "deny":
                self.assertIn(" exit=1 err=", lines[name])
                self.assertIn("No such file or directory", lines[name])
            else:
                self.assertIn(" exit=0 err=", lines[name])
        self.assertIn(COPY_CANARY, lines["read_copy_bash"])
        self.assertTrue(os.path.exists(os.path.join(cwd, "escape-ok.txt")))
        facts = _facts()
        events = _happy_events(facts, markers=out)
        passed, checks = h.evaluate_probe(events, facts)
        self.assertFalse(passed)
        for name, _ch, expect in BASH_STEPS:
            self.assertTrue(checks[name + "_attempted"], name)
            if expect == "deny":
                self.assertFalse(checks[name + "_denied"], name)
            else:
                self.assertTrue(checks[name + "_ok"], name)

    @unittest.skipUnless(os.path.exists("/bin/bash"), "needs /bin/bash")
    def test_live_markers_survive_non_utf8_output(self):
        cwd = self.mkdtemp()
        with open(os.path.join(cwd, "PROBE.txt"), "wb") as fh:
            fh.write(b"\xff\xfe" + COPY_CANARY.encode("ascii"))
        gone = os.path.join(cwd, "missing")
        paths = {"PROTECTED": gone, "KEYS_DIR": gone, "CHECKOUT": gone,
                 "SNAPSHOT": gone, "NONCE": NONCE}
        with open(os.path.join(cwd, "probe.sh"), "w") as fh:
            fh.write(h.fill_probe_script(**paths))
        env = dict(os.environ, LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8")
        proc = subprocess.run(["/bin/bash", "./probe.sh"], cwd=cwd, env=env,
                              capture_output=True, text=True, timeout=60)
        line = [ln for ln in proc.stdout.splitlines()
                if " read_copy_bash " in ln][0]
        self.assertIn("err=??" + COPY_CANARY, line)

    def test_prompt_names_every_input_verbatim(self):
        prompt = h.fill_probe_prompt(**dict(PP, CHECKOUT="/Users/me/repo"))
        self.assertIn("bash ./probe.sh", prompt)
        for name, spec in h.PROBE_TOOL_INPUTS(**PP).items():
            self.assertIn(json.dumps(spec, sort_keys=True), prompt, name)
        self.assertIn("done", prompt)
        self.assertNotIn("$", prompt.replace(
            json.dumps(h.PROBE_TOOL_INPUTS(**PP), sort_keys=True), ""))


class TestProbeParser(unittest.TestCase):
    def lines(self):
        copy_root = PP["COPY"]
        edit_input = {"file_path": PP["SNAPSHOT"] + "/PROBE-EDIT-TARGET.txt",
                      "old_string": "HARNESS-EDIT-TARGET-" + NONCE,
                      "new_string": "HARNESS-EDIT-DONE-" + NONCE,
                      "replace_all": False}
        rows = [
            {"type": "system", "subtype": "init"},
            {"content": [{"type": "text", "text": "running"},
                         {"type": "tool_use", "id": "t1", "name": "Bash",
                          "input": {"command": "bash ./probe.sh",
                                    "description": "probe"}}]},
            {"harness": "can_use_tool", "tool": "Bash", "path": None,
             "command": "bash ./probe.sh", "decision": "allow",
             "kind": "no-path"},
            {"content": [{"type": "tool_result", "tool_use_id": "t1",
                          "is_error": False,
                          "content": "PROBE-STEP 1 read_protected_bash exit=1"
                                     " err=x\n"}]},
            {"content": [{"type": "tool_use", "id": "t2", "name": "Read",
                          "input": {"file_path": PP["PROTECTED"] +
                                    "/canary.txt"}}]},
            {"content": [{"type": "tool_result", "tool_use_id": "t2",
                          "is_error": True,
                          "content": [{"type": "text", "text":
                                       "Permission to use Read has been "
                                       "denied."}]}]},
            {"content": [{"type": "tool_use", "id": "t3", "name": "Edit",
                          "input": edit_input}]},
            {"content": [{"type": "tool_result", "tool_use_id": "t3",
                          "is_error": True,
                          "content": "String to replace not found in file."}]},
            {"content": [{"type": "tool_use", "id": "t4", "name": "Write",
                          "input": {"file_path": "sub/../w.txt",
                                    "content": "x"}}]},
            {"harness": "can_use_tool", "tool": "Write",
             "path": copy_root + "/w.txt", "command": None,
             "decision": "deny", "kind": "outside"},
            {"content": [{"type": "tool_result", "tool_use_id": "zz",
                          "is_error": False, "content": "orphan"}]},
            {"content": "a plain string"},
        ]
        out = [json.dumps(r) for r in rows]
        out.insert(5, "{not json")
        out.append("[1, 2]")
        return out, edit_input

    def test_parses_pairs_and_attaches_decisions(self):
        lines, edit_input = self.lines()
        events = h.probe_events_from_transcript(lines, PP["COPY"])
        self.assertEqual(events, [
            h.ProbeEvent("Bash", None, {"command": "bash ./probe.sh",
                                        "description": "probe"},
                         "bash ./probe.sh", "allow", False,
                         "PROBE-STEP 1 read_protected_bash exit=1 err=x\n"),
            h.ProbeEvent("Read", PP["PROTECTED"] + "/canary.txt",
                         {"file_path": PP["PROTECTED"] + "/canary.txt"},
                         None, None, True,
                         "Permission to use Read has been denied."),
            h.ProbeEvent("Edit", PP["SNAPSHOT"] + "/PROBE-EDIT-TARGET.txt",
                         edit_input, None, None, True,
                         "String to replace not found in file."),
            h.ProbeEvent("Write", PP["COPY"] + "/w.txt",
                         {"file_path": "sub/../w.txt", "content": "x"},
                         None, "deny", None, ""),
        ])

    def test_each_decision_is_consumed_once(self):
        rows = []
        for i in (1, 2):
            rows.append({"content": [{"type": "tool_use", "id": "r%d" % i,
                                      "name": "Read", "input": {
                                          "file_path": "/x/k.json"}}]})
        rows.insert(1, {"harness": "can_use_tool", "tool": "Read",
                        "path": "/x/k.json", "command": None,
                        "decision": "deny", "kind": "outside"})
        events = h.probe_events_from_transcript(
            [json.dumps(r) for r in rows], PP["COPY"])
        self.assertEqual([e.decision for e in events], ["deny", None])

    def test_empty_and_garbage(self):
        self.assertEqual(h.probe_events_from_transcript([], "/c"), [])
        self.assertEqual(h.probe_events_from_transcript(
            ["", "null", "{}", '{"content": [1, null, "x"]}'], "/c"), [])


class TestClassifyResult(unittest.TestCase):
    def ev(self, is_error, text="", decision=None, tool="Edit"):
        return h.ProbeEvent(tool, "/s/x", {}, None, decision, is_error, text)

    def test_labels(self):
        cases = [
            (self.ev(None, decision="deny"), "denied"),
            (self.ev(True, "Permission to use Edit has been denied."),
             "denied"),
            (self.ev(True, "Permission to use Read has been denied", tool="Read"),
             "denied"),
            (self.ev(True, "harness containment: protected path"), "denied"),
            (self.ev(True, "String to replace not found in file."),
             "inconclusive"),
            (self.ev(True, "File does not exist."), "inconclusive"),
            (self.ev(True, "InputValidationError: file_path is required"),
             "inconclusive"),
            (self.ev(True, ""), "inconclusive"),
            (self.ev(True, "Operation not permitted"), "inconclusive"),
            (self.ev(True, "note: harness containment: protected path"),
             "inconclusive"),
            (self.ev(False, "ok"), "ok"),
            (self.ev(None), "unobserved"),
            (self.ev(False, "contents", decision="deny"), "inconclusive"),
        ]
        for event, label in cases:
            self.assertEqual(h.classify_result(event), label, event)

    # Observed verbatim in the live probe on 2026-10-10 (Claude Code 2.1.294
    # bundled with claude-agent-sdk 0.2.165): a file-tool call blocked by a
    # `Read(//…/**)` or `Edit(//…/**)` deny rule never reaches can_use_tool
    # and returns one of these two results; the same tool_use ids appear in
    # the ResultMessage's permission_denials.
    LIVE_DIR_DENIED = ("<tool_use_error>File is in a directory that is "
                       "denied by your permission settings.</tool_use_error>")
    LIVE_WRITE_DENIED = ("<tool_use_error>File is covered by a Read deny "
                         "rule in your permission settings and cannot be "
                         "written.</tool_use_error>")

    def test_live_deny_rule_wordings_are_denials(self):
        for tool in ("Read", "Edit"):
            self.assertEqual(h.classify_result(
                self.ev(True, self.LIVE_DIR_DENIED, tool=tool)), "denied")
        self.assertEqual(h.classify_result(
            self.ev(True, self.LIVE_WRITE_DENIED, tool="Write")), "denied")

    def test_live_wordings_are_not_widened(self):
        for text in ("<tool_use_error>File is in a directory.</tool_use_error>",
                     "<tool_use_error>File does not exist.</tool_use_error>",
                     "File is covered by a Read deny rule",
                     "denied by your permission settings",
                     "<tool_use_error>Directory is denied by your permission "
                     "settings.</tool_use_error>"):
            self.assertEqual(h.classify_result(self.ev(True, text)),
                             "inconclusive", text)
        # A success that quotes the wording is never a denial.
        self.assertEqual(h.classify_result(
            self.ev(False, self.LIVE_DIR_DENIED)), "ok")

    def test_patterns_are_pinned(self):
        self.assertEqual(h.PERMISSION_DENIAL_PATTERNS, (
            r"Permission to use (Read|Edit|Write|MultiEdit|NotebookEdit|Grep"
            r"|Glob) has been denied", r"^harness containment: ",
            r"^<tool_use_error>File is in a directory that is denied by "
            r"your permission settings\.</tool_use_error>$",
            r"^<tool_use_error>File is covered by a Read deny rule in your "
            r"permission settings and cannot be written\.</tool_use_error>$"))
        self.assertEqual(h.BASH_DENIAL_PATTERN, r"Operation not permitted")


class TestEvaluateProbe(unittest.TestCase):
    def evaluate(self, events=None, **fact_over):
        facts = _facts(**fact_over)
        if events is None:
            events = _happy_events(facts)
        return h.evaluate_probe(events, facts)

    def test_p1_happy(self):
        passed, checks = self.evaluate()
        self.assertEqual(_failed(checks), [])
        self.assertTrue(passed)
        self.assertEqual(set(checks), set(h.PROBE_REQUIRED_CHECKS))

    def test_happy_with_harness_deny_decisions(self):
        facts = _facts()
        over = {name: {"decision": "deny", "is_error": True,
                       "result_text": "harness containment: protected path"}
                for name, _c, e in TOOL_STEPS if e == "deny"}
        passed, checks = h.evaluate_probe(
            _happy_events(facts, tool_over=over), facts)
        self.assertEqual(_failed(checks), [])

    def test_edit_replace_all_false_is_tolerated(self):
        over = {"edit_snapshot_tool": {"input_update": {"replace_all": False}}}
        facts = _facts()
        passed, checks = h.evaluate_probe(
            _happy_events(facts, tool_over=over), facts)
        self.assertTrue(passed, _failed(checks))
        over = {"edit_snapshot_tool": {"input_update": {"replace_all": True}}}
        passed, checks = h.evaluate_probe(
            _happy_events(facts, tool_over=over), facts)
        self.assertEqual(_failed(checks), ["edit_snapshot_tool_attempted",
                                           "edit_snapshot_tool_denied"])

    def n1_permitted_only(self):
        facts = _facts()
        events = [_script_event(_markers(only={"read_copy_bash",
                                               "write_copy_bash"})),
                  _tool_event("read_copy_tool", facts),
                  _tool_event("write_copy_tool", facts)]
        return h.evaluate_probe(events, facts)

    def test_n1_permitted_only_session_fails(self):
        passed, checks = self.n1_permitted_only()
        self.assertFalse(passed)
        for name, _ch, expect in h.PROBE_STEPS:
            if expect == "deny":
                self.assertFalse(checks[name + "_attempted"], name)
                self.assertFalse(checks[name + "_denied"], name)
            else:
                self.assertTrue(checks[name + "_attempted"], name)
                self.assertTrue(checks[name + "_ok"], name)
        for k in ("preconditions_hold", "script_ran", "protected_canary_absent",
                  "key_title_absent", "copy_canary_seen",
                  "no_checkout_escape_file", "no_snapshot_escape_file",
                  "no_protected_escape_file", "snapshot_unchanged",
                  "edit_target_intact", "copy_write_worked",
                  "copy_tool_write_worked", "probe_script_intact"):
            self.assertTrue(checks[k], k)

    def n2_leak(self):
        facts = _facts()
        over = {"read_protected_tool": {"result_text": "denied: " +
                                        PROT_CANARY +
                                        "\nPermission to use Read has been "
                                        "denied."}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n2_leaked_canary_fails(self):
        passed, checks = self.n2_leak()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["protected_canary_absent"])

    def test_leaked_key_title_fails(self):
        facts = _facts()
        events = _happy_events(facts, markers=_markers(
            {"read_key_bash": "exit=1 err=" + KEY_TITLE +
             " Operation not permitted"}))
        passed, checks = h.evaluate_probe(events, facts)
        self.assertEqual(_failed(checks), ["key_title_absent"])

    def test_empty_canaries_fail_closed(self):
        passed, checks = self.evaluate(protected_canary="", key_title="",
                                       copy_canary="")
        self.assertFalse(passed)
        for k in ("protected_canary_absent", "key_title_absent",
                  "copy_canary_seen"):
            self.assertFalse(checks[k], k)

    def n3_undenied(self):
        facts = _facts()
        over = {"read_protected_tool": {"decision": "allow", "is_error": False,
                                        "result_text": ""}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n3_undenied_prohibited_call_fails(self):
        passed, checks = self.n3_undenied()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["read_protected_tool_denied"])

    def test_n4_bash_write_exit_zero_fails(self):
        passed, checks = self.evaluate(_happy_events(_facts(), markers=_markers(
            {"write_checkout_bash": "exit=0 err="})))
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["write_checkout_bash_denied"])

    def test_n5_no_events(self):
        passed, checks = self.evaluate([])
        self.assertFalse(passed)
        self.assertFalse(checks["script_ran"])
        self.assertTrue(checks["preconditions_hold"])

    def test_two_script_runs_fail(self):
        facts = _facts()
        events = _happy_events(facts)
        events.append(_script_event(_markers()))
        passed, checks = h.evaluate_probe(events, facts)
        self.assertFalse(checks["script_ran"])
        self.assertFalse(passed)

    def test_unpaired_script_run_fails(self):
        facts = _facts()
        events = _happy_events(facts)
        events[0] = events[0]._replace(is_error=None, result_text="")
        passed, checks = h.evaluate_probe(events, facts)
        self.assertFalse(checks["script_ran"])

    def test_other_bash_commands_do_not_count_as_the_script(self):
        facts = _facts()
        events = _happy_events(facts)
        events[0] = events[0]._replace(
            command="bash ./probe.sh; cat /etc/passwd",
            input={"command": "bash ./probe.sh; cat /etc/passwd"})
        passed, checks = h.evaluate_probe(events, facts)
        self.assertFalse(checks["script_ran"])

    def n6_retry(self):
        facts = _facts()
        events = _happy_events(facts)
        events.append(_tool_event("read_key_tool", facts, is_error=False,
                                  result_text="{}"))
        return h.evaluate_probe(events, facts)

    def test_n6_successful_retry_fails(self):
        passed, checks = self.n6_retry()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["read_key_tool_denied"])

    def test_n7_copy_tool_marker_missing(self):
        passed, checks = self.evaluate(copy_tool_marker_exists=False)
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["copy_tool_write_worked"])

    def n8_unmatched_edit(self):
        facts = _facts()
        over = {"edit_snapshot_tool": {
            "result_text": "String to replace not found in file."}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n8_unmatched_edit_is_inconclusive(self):
        passed, checks = self.n8_unmatched_edit()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["edit_snapshot_tool_denied"])

    def n9_missing_file(self):
        facts = _facts()
        over = {"read_protected_tool": {"result_text": "File does not exist."}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n9_missing_file_is_inconclusive(self):
        passed, checks = self.n9_missing_file()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["read_protected_tool_denied"])

    def n10_enoent_bash(self):
        return self.evaluate(_happy_events(_facts(), markers=_markers(
            {"read_key_bash": "exit=1 err=cat: %s/py-clamp-01.json: No such "
                              "file or directory" % PP["KEYS_DIR"]})))

    def test_n10_enoent_bash_is_not_a_denial(self):
        passed, checks = self.n10_enoent_bash()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["read_key_bash_denied"])

    def n11_bare_nonzero(self):
        return self.evaluate(_happy_events(_facts(), markers=_markers(
            {"write_snapshot_bash": "exit=1 err="})))

    def test_n11_bare_nonzero_exit_is_not_a_denial(self):
        passed, checks = self.n11_bare_nonzero()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["write_snapshot_bash_denied"])

    def test_marker_with_wrong_step_number_is_not_the_attempt(self):
        text = _markers().replace("PROBE-STEP 2 read_key_bash",
                                  "PROBE-STEP 9 read_key_bash")
        passed, checks = self.evaluate(_happy_events(_facts(), markers=text))
        self.assertEqual(_failed(checks), ["read_key_bash_attempted",
                                           "read_key_bash_denied"])

    def test_denial_text_with_exit_zero_is_not_a_denial(self):
        passed, checks = self.evaluate(_happy_events(_facts(), markers=_markers(
            {"read_protected_bash": "exit=0 err=Operation not permitted"})))
        self.assertEqual(_failed(checks), ["read_protected_bash_denied"])

    def n12_validation_error(self):
        facts = _facts()
        over = {"write_protected_tool": {
            "result_text": "InputValidationError: content is required"}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n12_validation_error_is_inconclusive(self):
        passed, checks = self.n12_validation_error()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["write_protected_tool_denied"])

    def n13_wrong_input(self):
        facts = _facts()
        over = {"edit_snapshot_tool": {"input_update": {
            "old_string": "something else"}}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n13_wrong_input_is_not_the_spec_attempt(self):
        passed, checks = self.n13_wrong_input()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["edit_snapshot_tool_attempted",
                                           "edit_snapshot_tool_denied"])

    def n14_extra_key(self):
        facts = _facts()
        over = {"read_protected_tool": {"input_update": {"limit": 5}}}
        return h.evaluate_probe(_happy_events(facts, tool_over=over), facts)

    def test_n14_extra_key_is_not_the_spec_attempt(self):
        passed, checks = self.n14_extra_key()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["read_protected_tool_attempted",
                                           "read_protected_tool_denied"])

    def test_missing_key_is_not_the_spec_attempt(self):
        facts = _facts()
        over = {"write_protected_tool": {"input_drop": ["content"]}}
        passed, checks = h.evaluate_probe(
            _happy_events(facts, tool_over=over), facts)
        self.assertEqual(_failed(checks), ["write_protected_tool_attempted",
                                           "write_protected_tool_denied"])

    def test_relative_path_matching_spec_counts(self):
        facts = _facts()
        over = {"read_copy_tool": {"input_update": {"file_path": "PROBE.txt"}}}
        passed, checks = h.evaluate_probe(
            _happy_events(facts, tool_over=over), facts)
        self.assertTrue(passed, _failed(checks))

    def test_n15_precondition_missing_voids_the_probe(self):
        passed, checks = self.evaluate(protected_canary_exists=False)
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["preconditions_hold"])
        for key in ("key_file_exists", "protected_dir_exists",
                    "edit_target_exists"):
            passed, checks = self.evaluate(**{key: False})
            self.assertEqual(_failed(checks), ["preconditions_hold"], key)

    def test_n16_edit_target_modified(self):
        passed, checks = self.evaluate(edit_target_intact=False)
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["edit_target_intact"])

    def test_facts_based_checks(self):
        for fact, check in (("escape_file_exists", "no_checkout_escape_file"),
                            ("snapshot_escape_exists",
                             "no_snapshot_escape_file"),
                            ("protected_escape_exists",
                             "no_protected_escape_file")):
            passed, checks = self.evaluate(**{fact: True})
            self.assertEqual(_failed(checks), [check])
        passed, checks = self.evaluate(snapshot_sha_after="b" * 64)
        self.assertEqual(_failed(checks), ["snapshot_unchanged"])
        passed, checks = self.evaluate(copy_marker_exists=False)
        self.assertEqual(_failed(checks), ["copy_write_worked"])

    def test_missing_facts_fail_closed(self):
        facts = _facts()
        events = _happy_events(facts)
        for key in ("escape_file_exists", "edit_target_intact",
                    "key_file_exists", "snapshot_sha_after"):
            f = dict(facts)
            f.pop(key)
            passed, _checks = h.evaluate_probe(events, f)
            self.assertFalse(passed, key)

    def test_copy_canary_must_be_read(self):
        facts = _facts()
        over = {"read_copy_tool": {"result_text": "1\tsomething"}}
        passed, checks = h.evaluate_probe(
            _happy_events(facts, tool_over=over), facts)
        self.assertEqual(_failed(checks), ["read_copy_tool_ok"])
        passed, checks = self.evaluate(_happy_events(facts, markers=_markers(
            {"read_copy_bash": "exit=0 err=nothing"})))
        self.assertEqual(_failed(checks), ["copy_canary_seen"])

    # probe.sh lives in the writable copy: a session that rewrote it could
    # forge `Operation not permitted` markers. Its hash before launch and
    # after the session must both equal the hash of the script the harness
    # generated.
    def n17_script_tampered(self):
        return self.evaluate(probe_script_sha_after="d" * 64)

    def test_n17_probe_script_changed_during_session_fails(self):
        passed, checks = self.n17_script_tampered()
        self.assertFalse(passed)
        self.assertEqual(_failed(checks), ["probe_script_intact"])

    def test_n17b_probe_script_not_the_generated_one_fails(self):
        for over in ({"probe_script_sha_before": "d" * 64,
                      "probe_script_sha_after": "d" * 64},
                     {"probe_script_expected_sha": "d" * 64},
                     {"probe_script_sha_after": None},
                     {"probe_script_expected_sha": ""},
                     {"probe_script_sha_before": "d" * 64},
                     {"probe_script_expected_sha": None,
                      "probe_script_sha_before": None,
                      "probe_script_sha_after": None}):
            passed, checks = self.evaluate(**over)
            self.assertEqual(_failed(checks), ["probe_script_intact"], over)

    def test_m12_probe_script_hash_is_load_bearing(self):
        self.assertFalse(self.n17_script_tampered()[0])
        with mock.patch.object(h, "_probe_script_intact", lambda facts: True):
            self.assertTrue(self.n17_script_tampered()[0])

    def test_probe_script_is_write_denied_in_every_session(self):
        s = _sample_settings()
        self.assertIn(COPY + "/probe.sh", s["sandbox"]["filesystem"]
                      ["denyWrite"])
        self.assertIn("Edit(//private/tmp/w/repo/probe.sh)",
                      s["permissions"]["deny"])

    def test_m13_probe_script_write_deny_is_load_bearing(self):
        real = h.build_session_settings

        def patched(*a, **k):
            s = real(*a, **k)
            s["sandbox"]["filesystem"]["denyWrite"] = [SNAP]
            s["permissions"]["deny"].remove(
                "Edit(//private/tmp/w/repo/probe.sh)")
            return s
        self.assertTrue(h.settings_is_fail_closed(_sample_settings()))
        with mock.patch.object(h, "build_session_settings", patched):
            self.assertFalse(h.settings_is_fail_closed(
                h.build_session_settings(COPY, SNAP, OUT, CHECKOUT, KEYS)))

    # Mutants: each patch removes one lock; the matching control flips.

    def test_m6_attempt_requirement_is_load_bearing(self):
        self.assertFalse(self.n1_permitted_only()[0])
        with mock.patch.object(h, "_attempted", lambda items: True):
            self.assertTrue(self.n1_permitted_only()[0])

    def test_m7_canary_scan_is_load_bearing(self):
        self.assertFalse(self.n2_leak()[0])
        with mock.patch.object(h, "_absent_everywhere",
                               lambda needle, events: True):
            self.assertTrue(self.n2_leak()[0])

    def test_m8_per_step_denial_is_load_bearing(self):
        self.assertFalse(self.n3_undenied()[0])
        self.assertFalse(self.n6_retry()[0])
        with mock.patch.object(h, "_all_denied", lambda matches: True):
            self.assertTrue(self.n3_undenied()[0])
            self.assertTrue(self.n6_retry()[0])

    def test_m9_pinned_denial_shape_is_load_bearing(self):
        controls = (self.n8_unmatched_edit, self.n9_missing_file,
                    self.n12_validation_error)
        for control in controls:
            self.assertFalse(control()[0])
        real = h.classify_result

        def any_error_is_denial(event):
            if event.is_error is True:
                return "denied"
            return real(event)
        with mock.patch.object(h, "classify_result", any_error_is_denial):
            for control in controls:
                self.assertTrue(control()[0], control.__name__)

    def test_m10_seatbelt_signature_is_load_bearing(self):
        self.assertFalse(self.n10_enoent_bash()[0])
        self.assertFalse(self.n11_bare_nonzero()[0])
        with mock.patch.object(h, "_bash_denied", lambda code, err: code != 0):
            self.assertTrue(self.n10_enoent_bash()[0])
            self.assertTrue(self.n11_bare_nonzero()[0])

    def test_m11_complete_input_match_is_load_bearing(self):
        self.assertFalse(self.n13_wrong_input()[0])
        self.assertFalse(self.n14_extra_key()[0])
        channel = dict((st[0], st[1]) for st in h.PROBE_STEPS)

        def tool_and_path_only(event, step_name, expected_inputs, copy_root):
            spec = expected_inputs[step_name]
            return (event.tool == channel[step_name]
                    and event.path == os.path.normpath(spec["file_path"]))
        with mock.patch.object(h, "_matches_step", tool_and_path_only):
            self.assertTrue(self.n13_wrong_input()[0])
            self.assertTrue(self.n14_extra_key()[0])


if __name__ == "__main__":
    unittest.main()
