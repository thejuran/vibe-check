"""Tests for harness_fixture: the synthetic case and its disposable copies.

Run with bare `pytest -q` from this directory.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_fixture as hf  # noqa: E402

CASE = "py-clamp-01"


def _run(argv, cwd):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=60)


def _git(repo, *args):
    proc = subprocess.run(["git", *args], cwd=repo, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args, proc.stderr))
    return proc.stdout


def _case_bytes(*parts):
    return (hf.FIXTURES_DIR / CASE).joinpath(*parts).read_bytes()


def _copy_files(root):
    """Relative paths of every file in the copy outside .git/."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            out.append(os.path.relpath(os.path.join(dirpath, name), root))
    return sorted(out)


class TestConstantsAndRecipe(unittest.TestCase):
    def test_constants_are_absolute_existing_paths(self):
        for p in (hf.FIXTURES_DIR, hf.KEYS_DIR, hf.PLUGIN_SCRIPTS_DIR):
            self.assertIsInstance(p, Path)
            self.assertTrue(p.is_absolute(), p)
            self.assertTrue(p.is_dir(), p)
        self.assertTrue((hf.PLUGIN_SCRIPTS_DIR / "gitfixture.py").is_file())

    def test_load_recipe_has_every_contract_key(self):
        r = hf.load_recipe(CASE)
        for key in ("case_id", "fixed_file", "untouched_file", "test_cmd",
                    "defect_check", "hunk_lines", "sentinels", "gsd_phase_id"):
            self.assertIn(key, r)
        self.assertEqual(r["case_id"], CASE)
        self.assertIsInstance(r["test_cmd"], list)
        self.assertIsInstance(r["defect_check"], list)
        self.assertEqual(set(r["sentinels"]),
                         {"staged", "unstaged_untouched", "unstaged_fixed"})

    def test_load_recipe_rejects_path_like_or_unknown_ids(self):
        for bad in ("../keys", "py-clamp-01/..", "", ".", "..", "a b"):
            with self.assertRaises(ValueError, msg=bad):
                hf.load_recipe(bad)
        with self.assertRaises(FileNotFoundError):
            hf.load_recipe("no-such-case")


class TestDefaultMode(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.recipe = hf.load_recipe(CASE)
        self.info = hf.build_copy(self.recipe, "default", self._tmp.name)
        self.root = self.info.root

    def tearDown(self):
        self._tmp.cleanup()

    def test_copyinfo_shape(self):
        self.assertIsInstance(self.info, hf.CopyInfo)
        self.assertEqual(self.info._fields,
                         ("root", "base_sha", "head_sha", "phase_id"))
        self.assertEqual(Path(self.root),
                         Path(os.path.realpath(self._tmp.name)) / "repo")
        self.assertIsNone(self.info.phase_id)

    def test_two_commits_base_then_defect_on_main(self):
        self.assertEqual(_git(self.root, "branch", "--show-current").strip(),
                         "main")
        self.assertEqual(_git(self.root, "rev-parse", "HEAD").strip(),
                         self.info.head_sha)
        self.assertEqual(_git(self.root, "rev-parse", "HEAD~1").strip(),
                         self.info.base_sha)
        self.assertEqual(
            _git(self.root, "rev-list", "--count", "HEAD").strip(), "2")
        self.assertEqual(_git(self.root, "log", "-1", "--format=%s").strip(),
                         "introduce clamp")
        self.assertEqual(_git(self.root, "diff", "--name-only",
                              self.info.base_sha, "HEAD").split(),
                         [self.recipe["fixed_file"]])

    def test_defect_is_committed_at_head_and_base_is_clean(self):
        fixed = self.recipe["fixed_file"]
        head_blob = _git(self.root, "show", "HEAD:" + fixed).encode()
        base_blob = _git(self.root, "show",
                         self.info.base_sha + ":" + fixed).encode()
        self.assertEqual(head_blob, _case_bytes("defect", fixed))
        self.assertEqual(base_blob, _case_bytes("base", fixed))
        self.assertEqual(_git(self.root, "status", "--porcelain"), "")

    def test_gitignore_ignores_turingmind(self):
        lines = Path(self.root, ".gitignore").read_text().splitlines()
        self.assertIn(".turingmind/", lines)
        _git(self.root, "ls-files", "--error-unmatch", ".gitignore")
        os.makedirs(os.path.join(self.root, ".turingmind", "state"))
        Path(self.root, ".turingmind", "state", "x.json").write_text("{}")
        self.assertEqual(_git(self.root, "status", "--porcelain"), "")

    def test_test_cmd_and_defect_check_fail_on_the_defect(self):
        self.assertNotEqual(_run(self.recipe["test_cmd"], self.root).returncode,
                            0)
        self.assertNotEqual(
            _run(self.recipe["defect_check"], self.root).returncode, 0)

    def test_no_planning_dir(self):
        self.assertFalse(os.path.exists(os.path.join(self.root, ".planning")))


class TestGsdMode(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.recipe = hf.load_recipe(CASE)
        self.info = hf.build_copy(self.recipe, "gsd", self._tmp.name)
        self.root = self.info.root
        self.phase_rel = ".planning/phases/" + self.recipe["gsd_phase_id"]

    def tearDown(self):
        self._tmp.cleanup()

    def test_phase_id_and_phase_files(self):
        pid = self.recipe["gsd_phase_id"]
        self.assertEqual(self.info.phase_id, pid)
        for suffix in ("PLAN.md", "SUMMARY.md"):
            rel = "%s/%s-%s" % (self.phase_rel, pid, suffix)
            self.assertEqual(Path(self.root, rel).read_bytes(),
                             _case_bytes("gsd", suffix))
            _git(self.root, "ls-files", "--error-unmatch", rel)

    def test_phase_dir_resolves_like_00_scope(self):
        # 00-scope: find .planning/phases .planning/milestones -maxdepth 2
        # -type d -name "<arg>" -> exactly one directory.
        found = []
        for top in (".planning/phases", ".planning/milestones"):
            base = Path(self.root, top)
            if not base.is_dir():
                continue
            for p in base.rglob(self.info.phase_id):
                depth = len(p.relative_to(base).parts)
                if p.is_dir() and depth <= 2:
                    found.append(p.relative_to(self.root).as_posix())
        self.assertEqual(found, [self.phase_rel])

    def test_phase_range_contains_the_defect_commit(self):
        phase_start = _git(self.root, "log", "--reverse", "--format=%H", "--",
                           self.phase_rel).split()[0]
        self.assertNotEqual(phase_start, self.info.head_sha)
        self.assertNotEqual(phase_start, self.info.base_sha)
        in_range = _git(self.root, "rev-list",
                        phase_start + "..HEAD").split()
        self.assertEqual(in_range, [self.info.head_sha])
        # base -> phase docs -> defect, in that order
        self.assertEqual(
            _git(self.root, "rev-list", "--reverse",
                 self.info.base_sha + "..HEAD").split(),
            [phase_start, self.info.head_sha])
        self.assertEqual(_git(self.root, "diff", "--name-only", phase_start,
                              "HEAD").split(), [self.recipe["fixed_file"]])

    def test_defect_at_head_and_tests_fail(self):
        fixed = self.recipe["fixed_file"]
        self.assertEqual(_git(self.root, "show", "HEAD:" + fixed).encode(),
                         _case_bytes("defect", fixed))
        self.assertNotEqual(_run(self.recipe["test_cmd"], self.root).returncode,
                            0)
        self.assertEqual(_git(self.root, "status", "--porcelain"), "")


class TestSharedInvariants(unittest.TestCase):
    def setUp(self):
        self.recipe = hf.load_recipe(CASE)

    def test_fixture_self_check_hunk_covers_every_differing_line(self):
        fixed = self.recipe["fixed_file"]
        base = _case_bytes("base", fixed).decode().splitlines()
        defect = _case_bytes("defect", fixed).decode().splitlines()
        self.assertEqual(len(base), len(defect))
        diff_lines = [i + 1 for i, (a, b) in enumerate(zip(base, defect))
                      if a != b]
        start, end = self.recipe["hunk_lines"]
        self.assertTrue(diff_lines, "defect must differ from base")
        self.assertEqual(diff_lines, list(range(start, end + 1)))
        self.assertGreaterEqual(len(base), 25)

    def test_fix_is_real_in_both_modes(self):
        fixed = self.recipe["fixed_file"]
        for mode in ("default", "gsd"):
            with tempfile.TemporaryDirectory() as tmp:
                info = hf.build_copy(self.recipe, mode, tmp)
                self.assertNotEqual(
                    _run(self.recipe["defect_check"], info.root).returncode, 0)
                Path(info.root, fixed).write_bytes(_case_bytes("base", fixed))
                self.assertEqual(
                    _run(self.recipe["test_cmd"], info.root).returncode, 0,
                    mode)
                self.assertEqual(
                    _run(self.recipe["defect_check"], info.root).returncode, 0,
                    mode)

    def test_fixed_file_sentinel_is_at_least_5_lines_from_the_hunk(self):
        s = self.recipe["sentinels"]["unstaged_fixed"]
        self.assertEqual(s["file"], self.recipe["fixed_file"])
        start, end = self.recipe["hunk_lines"]
        distance = min(abs(s["after_line"] - n)
                       for n in range(start, end + 1))
        self.assertGreaterEqual(distance, 5)

    def test_sentinel_sites_exist_in_their_files(self):
        sites = self.recipe["sentinels"]
        self.assertEqual(sites["staged"]["file"], self.recipe["untouched_file"])
        self.assertEqual(sites["unstaged_untouched"]["file"],
                         self.recipe["untouched_file"])
        self.assertNotEqual(sites["staged"]["after_line"],
                            sites["unstaged_untouched"]["after_line"])
        for site in sites.values():
            n = len(_case_bytes("base", site["file"]).decode().splitlines())
            self.assertTrue(1 <= site["after_line"] <= n, site)

    def test_copy_is_key_free_pre_check(self):
        key_text = (hf.KEYS_DIR / (CASE + ".json")).read_text()
        key = json.loads(key_text)
        key_names = {p.name for p in hf.KEYS_DIR.iterdir()}
        for mode in ("default", "gsd"):
            with tempfile.TemporaryDirectory() as tmp:
                info = hf.build_copy(self.recipe, mode, tmp)
                files = _copy_files(info.root)
                self.assertNotIn("recipe.json",
                                 {os.path.basename(f) for f in files})
                self.assertFalse(key_names & {os.path.basename(f)
                                              for f in files})
                for rel in files:
                    data = Path(info.root, rel).read_text()
                    self.assertNotIn("defect_check", data, rel)
                    self.assertNotIn(key["title"], data, rel)
                    self.assertNotIn(key["fix_hint"], data, rel)
                # the committed history is key-free too
                log = _git(info.root, "log", "-p", "--format=%B")
                self.assertNotIn("defect_check", log)
                self.assertNotIn(key["title"], log)

    def test_copy_skips_bytecode_caches_from_the_fixture(self):
        base_tests = hf.FIXTURES_DIR / CASE / "base" / "tests"
        cache = base_tests / "__pycache__"
        made = not cache.exists()
        cache.mkdir(exist_ok=True)
        # one stray only the directory skip catches, one only the suffix
        # skip catches, so each filter is exercised on its own
        in_cache = cache / "stray.txt"
        loose_pyc = base_tests / "stray.pyc"
        try:
            in_cache.write_bytes(b"x")
            loose_pyc.write_bytes(b"x")
            with tempfile.TemporaryDirectory() as tmp:
                info = hf.build_copy(self.recipe, "default", tmp)
                files = _copy_files(info.root)
                self.assertFalse(any("__pycache__" in f for f in files))
                self.assertFalse(any(f.endswith(".pyc") for f in files))
        finally:
            in_cache.unlink()
            loose_pyc.unlink()
            if made:
                cache.rmdir()

    def test_bad_mode_raises_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                hf.build_copy(self.recipe, "other", tmp)
            self.assertEqual(os.listdir(tmp), [])


class TestCli(unittest.TestCase):
    def test_cli_builds_a_copy_and_prints_copyinfo_json(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with tempfile.TemporaryDirectory() as tmp:
            proc = _run([sys.executable, os.path.join(here,
                                                      "harness_fixture.py"),
                         "--case", CASE, "--mode", "gsd", "--dest", tmp], here)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = json.loads(proc.stdout)
            self.assertEqual(set(out),
                             {"root", "base_sha", "head_sha", "phase_id"})
            self.assertEqual(out["phase_id"], "52-harness-case")
            self.assertEqual(_git(out["root"], "rev-parse", "HEAD").strip(),
                             out["head_sha"])

    def test_cli_bad_mode_exits_nonzero(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with tempfile.TemporaryDirectory() as tmp:
            proc = _run([sys.executable, os.path.join(here,
                                                      "harness_fixture.py"),
                         "--case", CASE, "--mode", "other", "--dest", tmp],
                        here)
            self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
