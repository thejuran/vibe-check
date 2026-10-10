"""Tests for harness_sentinels: three planted sentinels, verified byte for
byte, with plain reasons on any drift.

Run with bare `pytest -q` from this directory.
"""

import copy as copymod
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_fixture as hf  # noqa: E402
import harness_sentinels as hsn  # noqa: E402

CASE = "py-clamp-01"


def _git(repo, *args):
    proc = subprocess.run(["git", *args], cwd=repo, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args, proc.stderr))
    return proc.stdout


class _Planted(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.recipe = hf.load_recipe(CASE)
        self.copy = hf.build_copy(self.recipe, "default", self._tmp.name)
        self.record = hsn.plant(self.copy, self.recipe)
        self.untouched = Path(self.copy.root, self.recipe["untouched_file"])
        self.fixed = Path(self.copy.root, self.recipe["fixed_file"])

    def tearDown(self):
        self._tmp.cleanup()

    def _apply_fix(self):
        data = self.fixed.read_bytes()
        fixed = data.replace(b"    if value > hi - 1:\n        return hi - 1\n",
                             b"    if value > hi:\n        return hi\n")
        self.assertNotEqual(fixed, data)
        self.fixed.write_bytes(fixed)


class TestPlant(_Planted):
    def test_fixture_status_is_what_the_tests_assume(self):
        status = _git(self.copy.root, "status", "--porcelain")
        lines = sorted(status.splitlines())
        self.assertEqual(lines, sorted([
            " M %s" % self.recipe["fixed_file"],
            "MM %s" % self.recipe["untouched_file"],
        ]))
        staged = _git(self.copy.root, "diff", "--cached")
        unstaged = _git(self.copy.root, "diff")
        self.assertIn(self.record.staged_line, staged)
        self.assertNotIn(self.record.unstaged_line, staged)
        self.assertIn(self.record.unstaged_line, unstaged)
        self.assertIn(self.record.fixed_line, unstaged)
        self.assertNotIn(self.record.staged_line, unstaged)

    def test_sentinels_sit_where_the_recipe_says(self):
        sites = self.recipe["sentinels"]
        u = self.untouched.read_text(encoding="utf-8").splitlines()
        f = self.fixed.read_text(encoding="utf-8").splitlines()
        # S1 directly after its site; S2 after its site, shifted by S1.
        self.assertEqual(u[sites["staged"]["after_line"]],
                         self.record.staged_line)
        self.assertEqual(u[sites["unstaged_untouched"]["after_line"] + 1],
                         self.record.unstaged_line)
        self.assertEqual(f[sites["unstaged_fixed"]["after_line"]],
                         self.record.fixed_line)
        self.assertTrue(self.record.staged_line.startswith(
            "# sentinel-staged "))
        self.assertTrue(self.record.unstaged_line.startswith(
            "# sentinel-unstaged "))
        self.assertTrue(self.record.fixed_line.startswith(
            "# sentinel-fixed-file "))

    def test_record_holds_bytes_and_index_blob(self):
        self.assertEqual(self.record.untouched_bytes,
                         self.untouched.read_bytes())
        self.assertEqual(self.record.fixed_bytes, self.fixed.read_bytes())
        ls = _git(self.copy.root, "ls-files", "-s", "--",
                  self.recipe["untouched_file"])
        self.assertEqual(self.record.untouched_index_blob, ls.split()[1])

    def test_record_round_trips_through_json(self):
        text = self.record.to_json()
        json.loads(text)
        again = hsn.SentinelRecord.from_json(text)
        self.assertEqual(again, self.record)


class TestPlantRefusals(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.recipe = hf.load_recipe(CASE)
        self.copy = hf.build_copy(self.recipe, "default", self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_fixed_sentinel_near_the_hunk_is_refused(self):
        r = copymod.deepcopy(self.recipe)
        r["sentinels"]["unstaged_fixed"]["after_line"] = \
            r["hunk_lines"][1] + 4
        with self.assertRaises(hsn.SentinelError):
            hsn.plant(self.copy, r)
        self.assertEqual(_git(self.copy.root, "status", "--porcelain"), "")

    def test_fixed_sentinel_five_lines_away_is_allowed(self):
        r = copymod.deepcopy(self.recipe)
        r["sentinels"]["unstaged_fixed"]["after_line"] = \
            r["hunk_lines"][1] + 5
        hsn.plant(self.copy, r)

    def test_fixed_sentinel_before_the_hunk_is_measured_too(self):
        r = copymod.deepcopy(self.recipe)
        r["sentinels"]["unstaged_fixed"]["after_line"] = \
            r["hunk_lines"][0] - 3
        with self.assertRaises(hsn.SentinelError):
            hsn.plant(self.copy, r)

    def test_dirty_file_is_refused(self):
        p = Path(self.copy.root, self.recipe["untouched_file"])
        p.write_bytes(p.read_bytes() + b"# local edit\n")
        with self.assertRaises(hsn.SentinelError):
            hsn.plant(self.copy, self.recipe)

    def test_dirty_fixed_file_is_refused(self):
        p = Path(self.copy.root, self.recipe["fixed_file"])
        p.write_bytes(p.read_bytes() + b"# local edit\n")
        _git(self.copy.root, "add", self.recipe["fixed_file"])
        with self.assertRaises(hsn.SentinelError):
            hsn.plant(self.copy, self.recipe)


class TestVerify(_Planted):
    def test_untouched_plant_verifies_clean(self):
        self.assertEqual(hsn.verify(self.copy, self.record), [])

    def test_fix_inside_the_hunk_verifies_clean(self):
        self._apply_fix()
        self.assertEqual(hsn.verify(self.copy, self.record), [])

    def test_committed_fix_alone_verifies_clean(self):
        self._apply_fix()
        # Commit only the fix hunk, as fixstage does: HEAD + fix, no sentinel.
        head = _git(self.copy.root, "show",
                    "HEAD:%s" % self.recipe["fixed_file"])
        fixed_head = head.replace("    if value > hi - 1:\n        return hi - 1\n",
                                  "    if value > hi:\n        return hi\n")
        blob = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"], cwd=self.copy.root,
            input=fixed_head, capture_output=True, text=True,
            timeout=60).stdout.strip()
        _git(self.copy.root, "update-index", "--cacheinfo",
             "100644,%s,%s" % (blob, self.recipe["fixed_file"]))
        _git(self.copy.root, "commit", "-qm", "fix clamp")
        self.assertEqual(hsn.verify(self.copy, self.record), [])

    def test_flipped_byte_in_unstaged_sentinel_is_named(self):
        data = self.untouched.read_bytes()
        line = self.record.unstaged_line.encode("utf-8")
        flipped = line[:-1] + (b"0" if line[-1:] != b"0" else b"1")
        self.untouched.write_bytes(data.replace(line, flipped))
        reasons = hsn.verify(self.copy, self.record)
        self.assertIn("unstaged sentinel missing from %s"
                      % self.recipe["untouched_file"], reasons)

    def test_staged_sentinel_edit_is_named(self):
        data = self.untouched.read_bytes()
        line = self.record.staged_line.encode("utf-8")
        self.untouched.write_bytes(data.replace(line + b"\n", b""))
        reasons = hsn.verify(self.copy, self.record)
        self.assertIn("staged sentinel missing from %s"
                      % self.recipe["untouched_file"], reasons)

    def test_committed_fixed_file_sentinel_is_reported(self):
        self._apply_fix()
        _git(self.copy.root, "add", self.recipe["fixed_file"])
        _git(self.copy.root, "commit", "-qm", "fix clamp")
        reasons = hsn.verify(self.copy, self.record)
        self.assertIn("fixed-file sentinel was committed", reasons)

    def test_committed_staged_sentinel_is_reported(self):
        # A plain `git commit` takes the staged sentinel with it while the
        # index blob and the worktree bytes stay exactly as recorded.
        _git(self.copy.root, "commit", "-qm", "sweep")
        reasons = hsn.verify(self.copy, self.record)
        self.assertEqual(reasons, ["staged sentinel was committed"])

    def test_reset_untouched_file_changes_the_index_blob(self):
        _git(self.copy.root, "reset", "-q", "--",
             self.recipe["untouched_file"])
        self.assertEqual(self.untouched.read_bytes(),
                         self.record.untouched_bytes)
        reasons = hsn.verify(self.copy, self.record)
        self.assertEqual(reasons, ["staged sentinel index blob changed"])

    def test_mutant_without_the_index_blob_check_misses_the_reset(self):
        _git(self.copy.root, "reset", "-q", "--",
             self.recipe["untouched_file"])
        self.assertNotEqual(hsn.verify(self.copy, self.record), [])
        with mock.patch.object(hsn, "_index_blob_reasons",
                               return_value=[]):
            self.assertEqual(hsn.verify(self.copy, self.record), [])

    def test_edit_outside_the_hunk_in_the_fixed_file_is_reported(self):
        self._apply_fix()
        data = self.fixed.read_bytes()
        self.fixed.write_bytes(data.replace(b"exactly %s", b"exactly %r"))
        reasons = hsn.verify(self.copy, self.record)
        self.assertIn("%s changed outside the fix hunk"
                      % self.recipe["fixed_file"], reasons)

    def test_removed_fixed_file_sentinel_is_named(self):
        data = self.fixed.read_bytes()
        line = self.record.fixed_line.encode("utf-8") + b"\n"
        self.fixed.write_bytes(data.replace(line, b""))
        reasons = hsn.verify(self.copy, self.record)
        self.assertIn("fixed-file sentinel missing from %s"
                      % self.recipe["fixed_file"], reasons)

    def test_deleted_untouched_file_is_reported(self):
        self.untouched.unlink()
        reasons = hsn.verify(self.copy, self.record)
        self.assertIn("%s is missing" % self.recipe["untouched_file"],
                      reasons)

    def test_reasons_never_echo_file_content(self):
        self.untouched.write_bytes(b"secret payload\n")
        self.fixed.write_bytes(b"other payload\n")
        _git(self.copy.root, "add", "-A")
        _git(self.copy.root, "commit", "-qm", "wipe")
        reasons = hsn.verify(self.copy, self.record)
        self.assertTrue(reasons)
        for r in reasons:
            self.assertNotIn("payload", r)
            self.assertNotIn("sentinel-", r)

    def test_verify_writes_nothing(self):
        index = Path(self.copy.root, ".git", "index")
        before = (index.read_bytes(), index.stat().st_mtime_ns,
                  self.untouched.read_bytes(), self.fixed.read_bytes())
        hsn.verify(self.copy, self.record)
        after = (index.read_bytes(), index.stat().st_mtime_ns,
                 self.untouched.read_bytes(), self.fixed.read_bytes())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
