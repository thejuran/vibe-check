"""Isolation and record locks over the harness directory and its run records.

- No tracked file under docs/design/fix-harness/ names the benchmark or
  holdout inputs (the harness is proven on synthetic cases only).
- Every Phase-52 run record reads COMPLETE and fails validation only for
  the three freeze identity keys it predates (the schema is closed: a
  record without a verified manifest identity can no longer be written).

The forbidden patterns are built by concatenation so this file never spells
them, and the file excludes itself from the walk by name.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_fixture  # noqa: E402
import harness_record  # noqa: E402
import harness_sandbox  # noqa: E402

HARNESS_DIR = HERE.parent
REPO_ROOT = HARNESS_DIR.parent.parent.parent
RUNS_DIR = HARNESS_DIR / "runs" / "phase52"
RUN_IDS = ("P-D", "P-G", "C-D", "C-G")
PRESERVATION_IDS = ("P-D", "P-G")
CLEAN_IDS = ("C-D", "C-G")
SELF_NAME = Path(__file__).name
PRE_FREEZE_PROBLEMS = [
    "missing key: manifest_id", "missing key: check_digest",
    "missing key: candidate_sha",
    "manifest_id is not a sha256 hex digest",
    "check_digest is not a sha256 hex digest",
    "candidate_sha is not a 40-hex commit"]

HOLDOUT = "holdout-" + "v2.12"
ANSWER_KEY = "ANSWER-KEY-" + "b3"
FORBIDDEN = (
    HOLDOUT,
    "b3-ground-" + "truth",
    ANSWER_KEY,
)
SKIP_PARTS = (".venv", "__pycache__")


def isolation_hits(text):
    """The forbidden patterns that occur in `text`."""
    return [p for p in FORBIDDEN if p in text]


def tracked_harness_files():
    """Tracked files under the harness dir (git ls-files; argv list, so the
    gitignored venv and run copies are never listed)."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", "docs/design/fix-harness"],
        cwd=str(REPO_ROOT), capture_output=True, check=True, timeout=60)
    names = [n for n in out.stdout.decode("utf-8").split("\0") if n]
    files = []
    for name in names:
        parts = Path(name).parts
        if any(p in SKIP_PARTS for p in parts):
            continue
        if "runs" in parts and "copy" in parts:
            continue
        if Path(name).name == SELF_NAME:
            continue
        files.append(REPO_ROOT / name)
    return files


def _load(run_id):
    with open(RUNS_DIR / run_id / "run.json", encoding="utf-8") as fh:
        return json.load(fh)


class TestIsolation(unittest.TestCase):
    def test_no_b3_or_holdout_reference(self):
        files = tracked_harness_files()
        self.assertGreater(len(files), 20)  # the walk found the harness
        for path in files:
            text = path.read_bytes().decode("utf-8", errors="replace")
            with self.subTest(file=str(path.relative_to(REPO_ROOT))):
                self.assertEqual(isolation_hits(text), [])

    def test_fixture_not_derived_from_b3(self):
        for case_dir in sorted(harness_fixture.FIXTURES_DIR.iterdir()):
            recipe = case_dir / "recipe.json"
            if not recipe.is_file():
                continue
            with self.subTest(case=case_dir.name):
                data = json.loads(recipe.read_text(encoding="utf-8"))
                self.assertTrue(data["case_id"].startswith("py-"))
        keys = sorted(harness_fixture.KEYS_DIR.glob("*.json"))
        self.assertTrue(keys)
        for key in keys:
            data = json.loads(key.read_text(encoding="utf-8"))
            with self.subTest(key=key.name):
                lowered = {k.lower() for k in data}
                self.assertNotIn("diff_id", lowered)
                self.assertFalse(any("b3" in k for k in lowered))

    def test_mutant_holdout_text_is_a_hit(self):
        planted = "see docs/design/" + HOLDOUT + "/cases"
        self.assertEqual(isolation_hits(planted), [HOLDOUT])
        self.assertEqual(isolation_hits(ANSWER_KEY + ".md"), [ANSWER_KEY])
        self.assertEqual(isolation_hits("synthetic py-clamp-01"), [])


class TestSnapshotProvenance(unittest.TestCase):
    """The measured plugin copy is the commit's tree, outside the checkout."""

    def test_snapshot_source_is_the_commit(self):
        import shutil
        import tempfile
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
                              capture_output=True, check=True, timeout=60,
                              text=True).stdout.strip()
        dest = os.path.realpath(tempfile.mkdtemp(prefix="isolation-snap-"))
        self.addCleanup(shutil.rmtree, dest, True)
        snap = harness_sandbox.snapshot_plugin_from_commit(
            str(REPO_ROOT), "HEAD", dest)
        self.assertEqual(snap.source_path, "git:" + head)
        self.assertEqual(snap.git_sha, head)
        self.assertIs(snap.dirty, False)
        self.assertFalse(harness_sandbox._is_under(
            snap.path, os.path.realpath(str(REPO_ROOT))))
        listed = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "-z", "HEAD", "--",
             harness_sandbox.PLUGIN_REL], cwd=str(REPO_ROOT),
            capture_output=True, check=True, timeout=60).stdout
        want = sorted(n.decode("utf-8")[len(harness_sandbox.PLUGIN_REL) + 1:]
                      for n in listed.split(b"\0") if n)
        got = sorted(os.path.relpath(os.path.join(r, f), snap.path)
                     for r, _d, fs in os.walk(snap.path) for f in fs)
        self.assertEqual(got, want)


class TestRunRecords(unittest.TestCase):
    def test_phase52_records_valid(self):
        for run_id in RUN_IDS:
            with self.subTest(run=run_id):
                r = _load(run_id)
                self.assertEqual(harness_record.validate_record(r),
                                 PRE_FREEZE_PROBLEMS)
                r.update(manifest_id="d" * 64, check_digest="e" * 64,
                         candidate_sha=r["plugin_sha"])
                self.assertEqual(harness_record.validate_record(r), [])
                self.assertEqual(r["verdict"], "COMPLETE")
                self.assertEqual(r["reasons"], [])
                d = r["decisions"]
                self.assertEqual(r["would_be_owner_questions"],
                                 d["questions"] + d["turn_end_questions"]
                                 + d["repeats"])
                self.assertIsNone(r["waiting_on_owner_seconds"])
                self.assertEqual(r["execution_seconds_label"],
                                 "automated execution time")

    def test_entries_match_the_matrix(self):
        want = {"P-D": ("default", "preservation", "review"),
                "P-G": ("gsd", "preservation", "review"),
                "C-D": ("default", "clean", "finalize"),
                "C-G": ("gsd", "clean", "review")}
        for run_id, (mode, kind, entry) in want.items():
            r = _load(run_id)
            with self.subTest(run=run_id):
                self.assertEqual((r["mode"], r["kind"], r["entry"]),
                                 (mode, kind, entry))

    def test_clean_tree_runs_checkpointed(self):
        for run_id in CLEAN_IDS:
            with self.subTest(run=run_id):
                self.assertIs(_load(run_id)["clean_tree_checkpoint"]["passed"],
                              True)
        for run_id in PRESERVATION_IDS:
            with self.subTest(run=run_id):
                with open(RUNS_DIR / run_id / "sentinels.json",
                          encoding="utf-8") as fh:
                    sentinels = json.load(fh)
                planted = [sentinels[k] for k in
                           ("staged_line", "unstaged_line", "fixed_line")]
                self.assertTrue(all(isinstance(x, str) and x.strip()
                                    for x in planted))
                self.assertEqual(len(set(planted)), 3)
                # S1/S2 sit in the untouched file, S3 in the fixed file
                self.assertNotEqual(sentinels["untouched_file"],
                                    sentinels["fixed_file"])

    def test_mutant_waiting_time_fails_validation(self):
        r = dict(_load(RUN_IDS[0]))
        r["waiting_on_owner_seconds"] = 3.0
        self.assertIn("waiting_on_owner_seconds must be null (not measured)",
                      harness_record.validate_record(r))

    def test_mutant_failed_verdict_is_caught(self):
        r = dict(_load(RUN_IDS[0]))
        r["verdict"] = "FAILED"
        self.assertIn("verdict and reasons disagree",
                      harness_record.validate_record(r))


if __name__ == "__main__":
    unittest.main()
