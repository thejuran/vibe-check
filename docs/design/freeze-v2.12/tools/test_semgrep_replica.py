"""Tests for semgrep_replica: a fake semgrep on a test PATH (the real one is
never invoked), the degraded verdict classes, materialization containment,
the no-overwrite evidence writer, the import lock and a mutant proving the
error classification is load-bearing."""

import ast
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import semgrep_replica as sr  # noqa: E402
from freeze_common import FreezeError  # noqa: E402
from test_freeze_manifest import _Fixture, _run, _write  # noqa: E402

SR_PY = os.path.join(HERE, "semgrep_replica.py")

FAKE_SEMGREP = """#!/bin/sh
here=$(dirname "$0")
if [ "$1" = "--version" ]; then
  echo "1.136.0"
  exit 0
fi
printf '%s\\n' "$@" > "$here/argv.txt"
pwd > "$here/cwd.txt"
cat "$here/canned.json"
exit $(cat "$here/canned.rc")
"""

RESULT = {"check_id": "rules.example", "path": "new.py",
          "start": {"line": 1}, "end": {"line": 1}, "extra": {}}


class _Base(unittest.TestCase):
    """The shared fixture repo plus a third commit: `scripts/x.py` deleted,
    `agents/a.md` modified, `new.py` and `dir with space/b.py` added."""

    def setUp(self):
        self.fx = _Fixture()
        self.addCleanup(self.fx.close)
        r = self.fx.repo
        os.remove(os.path.join(r, "plugins/vibe-check/scripts/x.py"))
        _write(r, "plugins/vibe-check/agents/a.md", "changed\n")
        _write(r, "new.py", "import os\n")
        _write(r, "dir with space/b.py", "print(5)\n")
        _run(r, "git", "add", "-A")
        _run(r, "git", "commit", "-q", "-m", "c3")
        self.expected = sorted(["plugins/vibe-check/agents/a.md", "new.py",
                                "dir with space/b.py"])
        _write(self.fx.bin, "semgrep", FAKE_SEMGREP, mode=0o755)
        self.out_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.out_dir.cleanup)
        self.out = os.path.join(self.out_dir.name, "evidence.json")

    def canned(self, scanned=None, errors=None, results=None, rc=0):
        doc = {"paths": {"scanned": self.expected if scanned is None else scanned},
               "errors": [] if errors is None else errors,
               "results": [RESULT] if results is None else results}
        _write(self.fx.bin, "canned.json", json.dumps(doc))
        _write(self.fx.bin, "canned.rc", "%d\n" % rc)

    def main(self, *extra):
        argv = ["--repo", self.fx.repo, "--base", "HEAD~1", "--head", "HEAD",
                "--out", self.out, *extra]
        with mock.patch.dict(os.environ, self.fx.path_env()):
            return sr.main(argv)

    def evidence(self):
        with open(self.out, encoding="utf-8") as fh:
            return json.load(fh)


class TestRan(_Base):
    def test_ran_writes_evidence_and_exits_zero(self):
        self.canned()
        self.assertEqual(self.main(), 0)
        ev = self.evidence()
        self.assertEqual(ev["verdict"], "ran")
        self.assertEqual(ev["scanned_count"], 3)
        self.assertEqual(ev["intended_count"], 3)
        self.assertEqual(ev["missing_paths"], [])
        self.assertEqual(ev["version"], "1.136.0")
        self.assertIs(ev["rules_pinned"], False)
        head = sr.git(self.fx.repo, "rev-parse", "HEAD").decode().strip()
        self.assertEqual(ev["candidate_sha"], head)
        self.assertEqual(ev["range"]["head"], head)
        with open(os.path.join(self.fx.bin, "argv.txt")) as fh:
            argv = fh.read().splitlines()
        self.assertEqual(argv[:5], ["scan", "--json", "--config", "auto", "--"])
        self.assertEqual(sorted(argv[5:]), self.expected)

    def test_ran_with_findings_exit_one_and_benign_partial_parse(self):
        warn = {"level": "warn", "type": ["PartialParsing", [{"path": "new.py"}]]}
        self.canned(errors=[warn], rc=1)
        self.assertEqual(self.main(), 0)
        self.assertEqual(self.evidence()["verdict"], "ran")

    def test_ran_scratch_removed_and_working_tree_untouched(self):
        self.canned()
        before = sorted(os.listdir(self.fx.repo))
        self.assertEqual(self.main(), 0)
        with open(os.path.join(self.fx.bin, "cwd.txt")) as fh:
            cwd = fh.read().strip()
        self.assertFalse(os.path.exists(cwd))
        self.assertNotEqual(os.path.realpath(cwd),
                            os.path.realpath(self.fx.repo))
        self.assertEqual(sorted(os.listdir(self.fx.repo)), before)


class TestDegraded(_Base):
    def test_timeout_error_is_fatal_and_exits_one(self):
        self.canned(errors=[{"level": "error", "type": "Timeout"}], rc=1)
        self.assertEqual(self.main(), 1)
        ev = self.evidence()
        self.assertEqual(ev["verdict"], "degraded:fatal-errors")
        self.assertEqual(len(ev["fatal_errors"]), 1)

    def test_zero_scanned_is_degraded(self):
        self.canned(scanned=[])
        self.assertEqual(self.main(), 1)
        self.assertEqual(self.evidence()["verdict"], "degraded:zero-scanned")

    def test_zero_scanned_on_empty_range_is_degraded(self):
        self.canned(scanned=[])
        argv = ["--repo", self.fx.repo, "--base", "HEAD", "--head", "HEAD",
                "--out", self.out]
        with mock.patch.dict(os.environ, self.fx.path_env()):
            self.assertEqual(sr.main(argv), 1)
        self.assertEqual(self.evidence()["verdict"], "degraded:zero-scanned")

    def test_coverage_gap_names_the_missing_path(self):
        self.canned(scanned=[p for p in self.expected if p != "new.py"])
        self.assertEqual(self.main(), 1)
        ev = self.evidence()
        self.assertEqual(ev["verdict"], "degraded:coverage-gap")
        self.assertEqual(ev["missing_paths"], ["new.py"])

    def test_exit_two_is_degraded(self):
        self.canned(rc=2)
        self.assertEqual(self.main(), 1)
        self.assertEqual(self.evidence()["verdict"], "degraded:exit-2")

    def test_errors_without_results_are_all_fatal(self):
        warn = {"level": "warn", "type": ["PartialParsing", [{"path": "new.py"}]]}
        self.canned(errors=[warn], results=[])
        self.assertEqual(self.main(), 1)
        self.assertEqual(self.evidence()["verdict"], "degraded:fatal-errors")

    def test_unparseable_output_is_degraded(self):
        _write(self.fx.bin, "canned.json", "not json")
        _write(self.fx.bin, "canned.rc", "0\n")
        self.assertEqual(self.main(), 1)
        self.assertEqual(self.evidence()["verdict"], "degraded:fatal-errors")

    def test_absolute_scanned_paths_still_count(self):
        # semgrep may report paths under the scan root; normalized away.
        rec = {"fatal_errors": [], "intended_count": 1, "scanned_count": 1,
               "missing_paths": [], "exit_code": 0}
        self.assertEqual(sr.verdict(rec), "ran")
        self.assertEqual(sr._relpath("/s/x/new.py", "/s/x"), "new.py")
        self.assertEqual(sr._relpath("./-a.py", "/s/x"), "-a.py")


class TestTargets(_Base):
    def test_targets_only_files_existing_at_head(self):
        got = sr.targets(self.fx.repo, "HEAD~1", "HEAD")
        self.assertEqual(sorted(got), self.expected)
        self.assertNotIn("plugins/vibe-check/scripts/x.py", got)

    def test_targets_refuse_bad_revision(self):
        with self.assertRaises(FreezeError):
            sr.targets(self.fx.repo, "--output=x", "HEAD")


class TestContainment(_Base):
    def _refuses(self, path):
        with tempfile.TemporaryDirectory() as scratch:
            with self.assertRaises(FreezeError):
                sr.materialize(self.fx.repo, "HEAD", ["new.py", path], scratch)
            self.assertEqual(os.listdir(scratch), [])

    def test_containment_refuses_dotdot(self):
        self._refuses("a/../../evil.py")

    def test_containment_refuses_absolute(self):
        self._refuses("/tmp/evil.py")

    def test_containment_refuses_leading_dash(self):
        self._refuses("-dash.py")

    def test_containment_writes_head_blobs(self):
        with tempfile.TemporaryDirectory() as scratch:
            sr.materialize(self.fx.repo, "HEAD", self.expected, scratch)
            with open(os.path.join(scratch, "new.py"), "rb") as fh:
                self.assertEqual(fh.read(), b"import os\n")


class TestEvidenceWriter(_Base):
    def test_no_overwrite_writer_refuses_existing_file(self):
        _write(self.out_dir.name, "evidence.json", "keep\n")
        with self.assertRaises(FreezeError):
            sr.write_evidence(self.out, {"x": 1})
        with open(self.out) as fh:
            self.assertEqual(fh.read(), "keep\n")

    def test_no_overwrite_cli_exits_two_on_existing_file(self):
        self.canned()
        _write(self.out_dir.name, "evidence.json", "keep\n")
        self.assertEqual(self.main(), 2)
        with open(self.out) as fh:
            self.assertEqual(fh.read(), "keep\n")

    def test_usage_exit_two(self):
        with self.assertRaises(SystemExit) as cm:
            sr.main(["bogus"])
        self.assertEqual(cm.exception.code, 2)


class TestImportSet(unittest.TestCase):
    def test_import_set(self):
        with open(SR_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module.split(".")[0])
        allowed = {"argparse", "json", "os", "shutil", "subprocess", "sys",
                   "tempfile", "freeze_common"}
        self.assertTrue(names <= allowed, sorted(names - allowed))

    def test_import_set_shell_true_absent(self):
        with open(SR_PY, encoding="utf-8") as fh:
            self.assertNotIn("shell=True", fh.read())


class TestMutant(_Base):
    def test_mutant_ignoring_fatal_errors_flips_timeout(self):
        self.canned(errors=[{"level": "error", "type": "Timeout"}], rc=1)
        # Pristine: the timeout error degrades the run.
        self.assertEqual(self.main(), 1)
        self.assertEqual(self.evidence()["verdict"], "degraded:fatal-errors")
        os.remove(self.out)
        # Mutant: a classification that never calls an error fatal lets the
        # same run read as `ran` -- so the check is what blocks it.
        with mock.patch.object(sr, "classify_error", lambda e: None):
            self.assertEqual(self.main(), 0)
        self.assertEqual(self.evidence()["verdict"], "ran")


if __name__ == "__main__":
    unittest.main()
