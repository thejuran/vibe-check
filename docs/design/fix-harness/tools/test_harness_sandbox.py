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
                    "denyWrite": [SNAP],
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
                    "NotebookEdit",
                ],
                "defaultMode": "default",
            },
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

    def test_m5_skipping_fingerprint_comparison_accepts_stale_record(self):
        self.write_record(settings_fingerprint="0" * 64)
        self.assertTrue(self.run_preflight())
        with mock.patch.object(h, "_fingerprint_matches", lambda r, s: True):
            self.assertEqual(self.run_preflight(), [])


if __name__ == "__main__":
    unittest.main()
