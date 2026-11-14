"""Tests for path_records.py: the declared mode-path byte record at 2.14.1.

The committed record is re-derived from `git show` at the pinned commit on
every run, so these tests hold on any clone with full history.
"""

import ast
import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PATH_RECORDS_PY = os.path.join(HERE, "path_records.py")
BASELINE_DIR = os.path.join(HERE, "..", "baseline")
FOOTPRINT_JSON = os.path.join(BASELINE_DIR, "footprint-v2.14.1.json")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import path_records  # noqa: E402

# Pinned 2.14.1 figures: 62-CONTEXT.md, re-verified in 62-RESEARCH.md with
# `footprint.py --rev v2.14.1 --json`.
BASELINE = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"
PINNED = {
    "review-plain": (192057, 13),
    "deep-plain": (268997, 19),
    "finalize": (136114, 7),
}
ALL_MODES = {"review-plain", "review-all", "deep-plain", "deep-all", "finalize", "fix-loop"}


def git_bytes(rel):
    proc = subprocess.run(
        ["git", "-C", REPO, "show", "%s:plugins/vibe-check/%s" % (BASELINE, rel)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    return proc.stdout


def load_footprint():
    with open(FOOTPRINT_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def run_quiet(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = path_records.run(argv)
    return code, out.getvalue(), err.getvalue()


class TestFootprintRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = path_records.footprint_record(REPO, BASELINE)

    def test_constants(self):
        self.assertEqual(path_records.BASELINE_COMMIT, BASELINE)
        self.assertEqual(path_records.SCHEMA, 1)
        self.assertEqual(path_records.REQUIRED, {
            "review-plain": "plain review", "deep-plain": "deep review",
            "finalize": "Finalize"})

    def test_shape(self):
        rec = self.rec
        self.assertEqual(rec["schema"], 1)
        self.assertEqual(rec["baseline_commit"], BASELINE)
        self.assertTrue(rec["source"])
        self.assertEqual(set(rec["paths"]), ALL_MODES)
        for mode, entry in rec["paths"].items():
            self.assertEqual(entry["file_count"], len(entry["files"]), mode)
            self.assertEqual(entry["total_bytes"], sum(f["bytes"] for f in entry["files"]))
            self.assertEqual(entry["total_words"], sum(f["words"] for f in entry["files"]))
            for row in entry["files"]:
                self.assertEqual(set(row) >= {"path", "bytes", "words"}, True)
        for mode, label in path_records.REQUIRED.items():
            self.assertEqual(rec["paths"][mode]["label"], label)

    def test_pinned_totals(self):
        for mode, (total, count) in PINNED.items():
            entry = self.rec["paths"][mode]
            self.assertEqual((entry["total_bytes"], entry["file_count"]), (total, count), mode)

    def test_proxies_held_apart(self):
        self.assertNotIn("token", json.dumps(self.rec["paths"]))
        self.assertIn("PROXY", self.rec["proxies"]["label"])
        self.assertEqual(self.rec["proxies"]["label"],
                         "PROXY — derived from bytes, not measured, not a bill")
        self.assertIn("tokens@3.5", json.dumps(self.rec["proxies"]))

    def test_no_price(self):
        self.assertNotIn("$", json.dumps(self.rec))

    def test_verify_fresh_record(self):
        self.assertEqual(path_records.verify_footprint(REPO, self.rec), [])


class TestCommittedFootprint(unittest.TestCase):
    def test_committed_record_verifies(self):
        self.assertEqual(path_records.verify_footprint(REPO, load_footprint()), [])

    def test_committed_record_equals_fresh_capture(self):
        self.assertEqual(load_footprint(), path_records.footprint_record(REPO, BASELINE))

    def test_committed_pinned_totals(self):
        paths = load_footprint()["paths"]
        for mode, (total, count) in PINNED.items():
            self.assertEqual((paths[mode]["total_bytes"], paths[mode]["file_count"]),
                             (total, count), mode)

    def test_independent_finalize_recount(self):
        # Recounted from git without calling the module under test.
        files = load_footprint()["paths"]["finalize"]["files"]
        total = sum(len(git_bytes(f["path"])) for f in files)
        self.assertEqual(total, PINNED["finalize"][0])
        self.assertEqual(total, load_footprint()["paths"]["finalize"]["total_bytes"])

    def test_committed_file_format(self):
        with open(FOOTPRINT_JSON, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(text, json.dumps(json.loads(text), indent=2, sort_keys=True,
                                          ensure_ascii=False) + "\n")


class TestFootprintTamper(unittest.TestCase):
    def setUp(self):
        self.rec = load_footprint()

    def test_byte_changed_by_one_named(self):
        m = copy.deepcopy(self.rec)
        row = m["paths"]["finalize"]["files"][3]
        row["bytes"] += 1
        self.assertNotEqual(m, self.rec)
        problems = path_records.verify_footprint(REPO, m)
        self.assertTrue(any("finalize" in p and row["path"] in p for p in problems), problems)

    def test_file_removed_named(self):
        m = copy.deepcopy(self.rec)
        gone = m["paths"]["deep-plain"]["files"].pop(5)
        self.assertNotEqual(m, self.rec)
        problems = path_records.verify_footprint(REPO, m)
        self.assertTrue(any("deep-plain" in p and gone["path"] in p for p in problems), problems)

    def test_total_bytes_changed_named(self):
        m = copy.deepcopy(self.rec)
        m["paths"]["review-plain"]["total_bytes"] -= 7
        self.assertNotEqual(m, self.rec)
        problems = path_records.verify_footprint(REPO, m)
        self.assertTrue(any("review-plain" in p and "total_bytes" in p for p in problems),
                        problems)


class TestFootprintCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.out = os.path.join(self.tmp, "fp.json")

    def test_capture_writes_record(self):
        code, _, _ = run_quiet(["footprint", "--repo", REPO, "--out", self.out])
        self.assertEqual(code, 0)
        with open(self.out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), load_footprint())

    def test_capture_guard_refuses_on_disagreement(self):
        fp = path_records.load_plugin_module(REPO, "footprint")
        real = fp.path_stats

        def plus_one(root, mode, rev=None):
            stats = real(root, mode, rev=rev)
            if mode == "finalize":
                stats["files"][0] = dict(stats["files"][0], bytes=stats["files"][0]["bytes"] + 1)
                stats["bytes"] += 1
            return stats

        with mock.patch.object(fp, "path_stats", plus_one):
            code, _, err = run_quiet(["footprint", "--repo", REPO, "--out", self.out])
        self.assertEqual(code, 1)
        self.assertIn("FOOTPRINT RECOUNT DISAGREES WITH footprint.py — STOPPING", err)
        self.assertFalse(os.path.exists(self.out))

    def test_unknown_commit_exit_2(self):
        code, _, _ = run_quiet(["footprint", "--repo", REPO, "--out", self.out,
                                "--commit", "0" * 40])
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.out))

    def test_unknown_commit_subprocess_exit_2(self):
        proc = subprocess.run(
            [sys.executable, PATH_RECORDS_PY, "footprint", "--repo", REPO, "--out", self.out,
             "--commit", "deadbeefnotacommit"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        self.assertEqual(proc.returncode, 2)


class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "hashlib", "json", "os", "subprocess", "sys",
               "footprint", "tracecheck"}

    def test_path_records_imports(self):
        with open(PATH_RECORDS_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        self.assertTrue(names <= self.ALLOWED, names - self.ALLOWED)


if __name__ == "__main__":
    unittest.main()
