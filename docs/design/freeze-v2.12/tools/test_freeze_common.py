"""Tests for freeze_common (git + hash helpers) and freeze_policy (path map)."""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import freeze_common  # noqa: E402
import freeze_policy  # noqa: E402
from freeze_common import FreezeError  # noqa: E402

PATH_MAP = os.path.join(os.path.dirname(HERE), "PATH-MAP.json")
RERUN = {"engineering", "detection", "workflow"}


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


class _Repo:
    """A throwaway git repo with a committed plugin tree."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        _run(self.root, "git", "init", "-q")
        _run(self.root, "git", "config", "user.email", "t@example.invalid")
        _run(self.root, "git", "config", "user.name", "t")
        _write(self.root, "plugins/vibe-check/agents/x.md",
               "---\nmodel: opus\n---\nbody\n")
        _write(self.root, "plugins/vibe-check/scripts/run.sh", "#!/bin/sh\n",
               mode=0o755)
        _write(self.root, "plugins/vibe-check/empty.txt", b"")
        _run(self.root, "git", "add", "-A")
        _run(self.root, "git", "commit", "-q", "-m", "c1")

    def close(self):
        self._tmp.cleanup()


class TestGitHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = _Repo()

    @classmethod
    def tearDownClass(cls):
        cls.repo.close()

    def test_tree_files_at_matches_live_files(self):
        tree = freeze_common.tree_files_at(self.repo.root, "HEAD",
                                           "plugins/vibe-check")
        live = freeze_common.live_files(
            os.path.join(self.repo.root, "plugins/vibe-check"))
        self.assertEqual({k: v["sha256"] for k, v in tree.items()}, live)
        self.assertEqual(set(tree), {"agents/x.md", "scripts/run.sh", "empty.txt"})

    def test_tree_files_at_records_modes(self):
        tree = freeze_common.tree_files_at(self.repo.root, "HEAD",
                                           "plugins/vibe-check")
        self.assertEqual(tree["scripts/run.sh"]["mode"], "100755")
        self.assertEqual(tree["agents/x.md"]["mode"], "100644")

    def test_tree_files_at_single_file_prefix(self):
        tree = freeze_common.tree_files_at(self.repo.root, "HEAD",
                                           "plugins/vibe-check/agents/x.md")
        self.assertEqual(set(tree), {"x.md"})

    def test_tree_files_at_absent_prefix_is_empty(self):
        self.assertEqual(freeze_common.tree_files_at(
            self.repo.root, "HEAD", "docs/nope"), {})

    def test_tree_files_at_pattern_lists_directory_entries(self):
        tree = freeze_common.tree_files_at(self.repo.root, "HEAD",
                                           "plugins/vibe-check", pattern="*.txt",
                                           recursive=False)
        self.assertEqual(set(tree), {"empty.txt"})

    def test_live_files_honors_excludes(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "a.py", "x")
            _write(d, "__pycache__/a.cpython.pyc", "x")
            _write(d, ".pytest_cache/v", "x")
            _write(d, "b.pyc", "x")
            _write(d, ".in_use", "x")
            self.assertEqual(set(freeze_common.live_files(d)), {"a.py"})

    def test_validate_rev_refuses_leading_dash_and_odd_chars(self):
        for bad in ("-x", "--output=/tmp/x", "a b", "a;b", "", "a$b"):
            with self.assertRaises(FreezeError):
                freeze_common.validate_rev(bad)
        self.assertEqual(freeze_common.validate_rev("HEAD~1"), "HEAD~1")

    def test_validate_rel_refuses_dotdot(self):
        for bad in ("../x", "a/../b", "/abs", "a//b", "a\nb"):
            with self.assertRaises(FreezeError):
                freeze_common.validate_rel(bad)

    def test_git_failure_raises(self):
        with self.assertRaises(FreezeError):
            freeze_common.git(self.repo.root, "rev-parse", "--verify", "nope^{commit}")

    def test_resolve_rev_full_shas(self):
        sha, tree = freeze_common.resolve_rev(self.repo.root, "HEAD")
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertRegex(tree, r"^[0-9a-f]{40}$")

    def test_blob_at(self):
        self.assertEqual(freeze_common.blob_at(
            self.repo.root, "HEAD", "plugins/vibe-check/agents/x.md"),
            b"---\nmodel: opus\n---\nbody\n")
        self.assertIsNone(freeze_common.blob_at(self.repo.root, "HEAD", "nope.md"))


class TestHashing(unittest.TestCase):
    def test_tree_sha256_of_map_order_insensitive(self):
        a = {"x": "1" * 64, "y": "2" * 64}
        b = {"y": "2" * 64, "x": "1" * 64}
        self.assertEqual(freeze_common.tree_sha256_of_map(a),
                         freeze_common.tree_sha256_of_map(b))
        self.assertNotEqual(freeze_common.tree_sha256_of_map(a),
                            freeze_common.tree_sha256_of_map({"x": "1" * 64}))

    def test_canonical_json(self):
        self.assertEqual(freeze_common.canonical_json({"b": 1, "a": "é"}),
                         '{"a":"é","b":1}')

    def test_glob_to_regex(self):
        g = freeze_common.glob_to_regex
        self.assertTrue(g("a/**").match("a/b/c"))
        self.assertFalse(g("a/*").match("a/b/c"))
        self.assertTrue(g("a/**/c").match("a/c"))
        self.assertTrue(g("runs*/**").match("runs-v2/x"))
        self.assertFalse(g("a.md").match("aXmd"))

    def test_resolve_homes(self):
        env = dict(os.environ)
        env.pop("CODEX_HOME", None)
        from unittest import mock
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(freeze_common.resolve_homes("/x", None),
                             ("/x", "/x/.codex"))
            home = os.path.expanduser("~")
            self.assertEqual(freeze_common.resolve_homes(None, None),
                             (home, os.path.join(home, ".codex")))


class TestPathMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pm = freeze_policy.load_path_map(PATH_MAP)

    def _base(self):
        with open(PATH_MAP, encoding="utf-8") as fh:
            return json.load(fh)

    def test_real_map_loads_with_enough_rules(self):
        self.assertGreaterEqual(len(self.pm["rules"]), 40)

    def test_union_over_matching_rules(self):
        pm = self._base()
        pm["rules"] = [{"glob": "a/**", "cats": ["engineering"]},
                       {"glob": "a/b.py", "cats": ["detection"]}]
        out = freeze_policy.classify(["a/b.py", "a/c.py"],
                                     freeze_policy.validate_path_map(pm))
        self.assertEqual(out["a/b.py"], {"engineering", "detection"})
        self.assertEqual(out["a/c.py"], {"engineering"})

    def test_unmapped_is_every_rerun_category(self):
        out = freeze_policy.classify(["somewhere/new.txt"], self.pm)
        self.assertEqual(out["somewhere/new.txt"], RERUN)

    def test_reporting_paths(self):
        out = freeze_policy.classify(
            ["README.md", "docs/design/freeze-v2.12/FREEZE-MANIFEST-1.json",
             "plugins/vibe-check/docs/efficacy/RESULTS-v2.12.md"], self.pm)
        for cats in out.values():
            self.assertEqual(cats, {"reporting"})

    def test_combined_categories(self):
        out = freeze_policy.classify(
            ["plugins/vibe-check/scripts/score.py",
             "docs/design/fix-harness/tools/x.py",
             "plugins/vibe-check/agents/bugs.md",
             "plugins/vibe-check/scripts/test_score.py"], self.pm)
        self.assertEqual(out["plugins/vibe-check/scripts/score.py"],
                         {"engineering", "detection"})
        self.assertEqual(out["docs/design/fix-harness/tools/x.py"],
                         {"engineering", "workflow"})
        self.assertEqual(out["plugins/vibe-check/agents/bugs.md"], RERUN)
        self.assertEqual(out["plugins/vibe-check/scripts/test_score.py"],
                         {"engineering"})

    def test_map_self_protection(self):
        out = freeze_policy.classify([freeze_policy.MAP_SELF_PATH], self.pm)
        self.assertEqual(out[freeze_policy.MAP_SELF_PATH], RERUN)
        rule = [r for r in self.pm["rules"]
                if r["glob"] == freeze_policy.MAP_SELF_PATH]
        self.assertEqual(len(rule), 1)
        self.assertEqual(set(rule[0]["cats"]), RERUN)

    def test_map_self_protection_survives_a_lowering_edit(self):
        pm = self._base()
        pm["rules"] = [{"glob": freeze_policy.MAP_SELF_PATH, "cats": ["reporting"]}]
        out = freeze_policy.classify([freeze_policy.MAP_SELF_PATH],
                                     freeze_policy.validate_path_map(pm))
        self.assertTrue(RERUN <= out[freeze_policy.MAP_SELF_PATH])

    def test_mutant_empty_unmapped_rejected(self):
        pm = self._base()
        pm["unmapped"] = []
        with self.assertRaises(FreezeError):
            freeze_policy.validate_path_map(pm)

    def test_partial_unmapped_rejected(self):
        pm = self._base()
        pm["unmapped"] = ["engineering"]
        with self.assertRaises(FreezeError):
            freeze_policy.validate_path_map(pm)

    def test_bad_shapes_rejected(self):
        for edit in (lambda d: d.update(schema="x"),
                     lambda d: d["categories"].pop("reporting"),
                     lambda d: d["rules"].append({"glob": "x", "cats": []}),
                     lambda d: d["rules"].append({"glob": "x", "cats": ["bogus"]}),
                     lambda d: d["rules"].append({"glob": "x", "cats": ["reporting"],
                                                  "extra": 1}),
                     lambda d: d.update(extra=1)):
            pm = self._base()
            edit(pm)
            with self.assertRaises(FreezeError):
                freeze_policy.validate_path_map(pm)

    def test_required(self):
        req = freeze_policy.required({"engineering", "reporting"})
        self.assertEqual(set(req), {"engineering"})
        self.assertEqual(len(freeze_policy.required(RERUN)["detection"]), 6)
        self.assertEqual(len(freeze_policy.required(RERUN)["workflow"]), 18)
        self.assertEqual(freeze_policy.required({"reporting"}), {})


def _imports(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestImportSet(unittest.TestCase):
    def test_freeze_common_imports(self):
        got = _imports(os.path.join(HERE, "freeze_common.py"))
        self.assertTrue(got <= {"hashlib", "json", "os", "re", "subprocess"}, got)

    def test_freeze_policy_imports(self):
        got = _imports(os.path.join(HERE, "freeze_policy.py"))
        self.assertTrue(got <= {"fnmatch", "json", "os", "re", "freeze_common"}, got)


if __name__ == "__main__":
    unittest.main()
