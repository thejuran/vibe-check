"""Tests for harness_sandbox: the containment policy every harness session runs under.

Run with bare `pytest -q` from this directory. Every lock has a mutant test that
patches the lock out and asserts the outcome flips.
"""

import copy
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


if __name__ == "__main__":
    unittest.main()
