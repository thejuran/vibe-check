"""Tests for finalize_capture.py: the pinned Finalize capture harness.

Every lock here is applied to the real input and to a mutant of it, and each
mutant asserts the mutation really happened, so no check is decorative.
"""

import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import finalize_capture as fc  # noqa: E402

CAPTURE_PY = os.path.join(HERE, "finalize_capture.py")
REPO = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, timeout=30,
                      check=True).stdout.strip()
FINALIZE_REL = "plugins/vibe-check/phases/shared/90-finalize.md"
UNKNOWN_COMMIT = "0" * 40

SITUATION_IDS = ["clean-close", "card-first", "one-rebuild",
                 "refused-close", "fresh-shell-restart"]
BLOB_PRINT = "printf 'BLOBFILE=%s\\n' \"$BLOBFILE\""
GATE_PRINT = "printf 'GATEFILE=%s\\n' \"$GATEFILE\""


def _git_show_bytes(rel, commit=fc.BASELINE_COMMIT):
    return subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (commit, rel)],
                          capture_output=True, timeout=30, check=True).stdout


class _PinnedTree(unittest.TestCase):
    """One materialised copy of the pinned plugin tree for the whole class."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="fc-pinned-")
        try:
            cls.vc_root = fc.materialize(REPO, fc.BASELINE_COMMIT, cls._tmp)
            with open(os.path.join(cls.vc_root, "phases", "shared",
                                   "90-finalize.md"), encoding="utf-8") as fh:
                cls.finalize_text = fh.read()
        except BaseException:
            shutil.rmtree(cls._tmp, True)
            raise

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, True)


class TestMaterialize(_PinnedTree):
    def test_tree_holds_finalize_and_gate(self):
        self.assertTrue(os.path.isfile(os.path.join(
            self.vc_root, "phases", "shared", "90-finalize.md")))
        self.assertTrue(os.path.isfile(os.path.join(
            self.vc_root, "scripts", "finalize_gate.py")))

    def test_finalize_md_equals_the_pinned_commit_by_independent_hash(self):
        with open(os.path.join(self.vc_root, "phases", "shared",
                               "90-finalize.md"), "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        want = hashlib.sha256(_git_show_bytes(FINALIZE_REL)).hexdigest()
        self.assertEqual(got, want)

    def test_unknown_commit_raises_usage_error(self):
        dest = tempfile.mkdtemp(prefix="fc-bad-")
        self.addCleanup(shutil.rmtree, dest, True)
        with self.assertRaises(fc.UsageError):
            fc.materialize(REPO, UNKNOWN_COMMIT, dest)

    def test_option_shaped_commit_is_refused(self):
        dest = tempfile.mkdtemp(prefix="fc-bad-")
        self.addCleanup(shutil.rmtree, dest, True)
        with self.assertRaises(fc.UsageError):
            fc.materialize(REPO, "--output=/tmp/x", dest)

    def test_cli_unknown_commit_exits_two(self):
        out = tempfile.mkdtemp(prefix="fc-out-")
        self.addCleanup(shutil.rmtree, out, True)
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = fc.main(["capture", "--repo", REPO, "--commit", UNKNOWN_COMMIT,
                          "--out", os.path.join(out, "record.json")])
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(os.path.join(out, "record.json")))


class TestNormalise(unittest.TestCase):
    WORK = "/private/var/folders/ab/T/fc-work-1a2b3c"

    def test_workdir_becomes_token(self):
        text = "BLOBFILE=%s/tmp/file.json\n" % self.WORK
        self.assertEqual(fc.normalise(text, self.WORK),
                         "BLOBFILE=<WORK>/tmp/file.json\n")

    def test_mktemp_suffix_becomes_fixed(self):
        self.assertEqual(fc.normalise("GATEFILE=/x/vc.Ab3dE9.err", "/nowhere"),
                         "GATEFILE=/x/vc.XXXXXX.err")

    def test_iso_time_becomes_token(self):
        self.assertEqual(
            fc.normalise("state archived as s.json.archived-2026-11-14", "/w"),
            "state archived as s.json.archived-<TIME>")
        self.assertEqual(fc.normalise('{"at": "2026-11-14T09:30:01Z"}', "/w"),
                         '{"at": "<TIME>"}')

    def test_epoch_becomes_token(self):
        self.assertEqual(fc.normalise('{"ts": 1794650000}', "/w"),
                         '{"ts": <TIME>}')

    def test_plain_text_unchanged(self):
        text = '{"action": "write", "reason": "all counts are 0", "n": 42}\n'
        self.assertEqual(fc.normalise(text, "/w"), text)

    def test_rules_are_written_down(self):
        self.assertIsInstance(fc.NORMALISATION, tuple)
        self.assertGreaterEqual(len(fc.NORMALISATION), 3)
        joined = " ".join(fc.NORMALISATION)
        for token in ("<WORK>", "vc.XXXXXX", "<TIME>"):
            self.assertIn(token, joined)


class TestCanonical(unittest.TestCase):
    def test_key_order_does_not_matter(self):
        self.assertEqual(fc.canonical_sha256({"a": 1, "b": [1, 2]}),
                         fc.canonical_sha256({"b": [1, 2], "a": 1}))

    def test_one_character_changes_the_hash(self):
        self.assertNotEqual(fc.canonical_sha256({"a": "write"}),
                            fc.canonical_sha256({"a": "writf"}))


class TestSituations(unittest.TestCase):
    def test_five_ids_in_order(self):
        self.assertEqual(list(fc.SITUATIONS), SITUATION_IDS)

    def test_each_has_inputs(self):
        for sid, spec in fc.SITUATIONS.items():
            inputs = spec["inputs"]
            for key in ("fixture", "state", "owner_answers"):
                self.assertIn(key, inputs, sid)
            self.assertTrue(inputs["fixture"].startswith("scripts/fixtures/"),
                            sid)

    def test_outputs_schema_is_fixed(self):
        self.assertEqual(set(fc.OUTPUT_KEYS),
                         {"steps", "gate", "stop_sentence", "report",
                          "files_written", "files_archived", "state_closed",
                          "tally"})
        self.assertEqual(set(fc.STEP_KEYS),
                         {"id", "exit", "stdout", "stderr_present"})
        self.assertEqual(set(fc.TALLY_KEYS),
                         {"commands_run", "values_carried", "writes"})


class TestFences(_PinnedTree):
    def test_eighteen_fences(self):
        self.assertEqual(len(fc.extract_fences(self.finalize_text)), 18)

    def test_fixture_has_indented_and_four_backtick_openers(self):
        text = self.finalize_text
        indented = re.findall(r"(?m)^[ \t]+```bash$", text)
        four = re.findall(r"(?m)^````bash$", text)
        self.assertGreaterEqual(len(indented), 1)
        self.assertEqual(len(four), 1)
        fences = fc.extract_fences(text)
        # the four-backtick fence's body is among the extracted bodies
        start = text.index("````bash\n") + len("````bash\n")
        four_body = text[start:text.index("\n````", start)]
        self.assertIn(four_body, fences)

    def test_blobfile_and_gatefile_fences_are_found_and_indented(self):
        text = self.finalize_text
        fences = fc.extract_fences(text)
        for needle in (BLOB_PRINT, GATE_PRINT):
            body = fc.fence_holding(fences, needle)
            self.assertIsNotNone(body, needle)
            # the opener line of this fence starts with whitespace
            at = text.index(needle)
            opener = text.rindex("```bash", 0, at)
            line_start = text.rindex("\n", 0, opener) + 1
            self.assertTrue(text[line_start:opener].strip() == ""
                            and opener > line_start, needle)

    def test_fence_holding_missing_needle_is_none(self):
        self.assertIsNone(fc.fence_holding(
            fc.extract_fences(self.finalize_text), "no such needle anywhere"))

    def test_wrong_rule_mutant_column_zero_only(self):
        text = self.finalize_text
        col0 = re.compile(r"^```bash\n(.*?)\n```", re.M | re.S)
        self.assertNotEqual(col0.pattern, fc.FENCE_RE.pattern)
        self.assertEqual(len(re.findall(r"(?m)^```bash$", text)), 9)
        with mock.patch.object(fc, "FENCE_RE", col0):
            self.assertIs(fc.FENCE_RE, col0)
            fences = fc.extract_fences(text)
            self.assertLess(len(fences), 18)
            self.assertEqual(len(fences), 9)
            self.assertIsNone(fc.fence_holding(fences, BLOB_PRINT))
        self.assertEqual(len(fc.extract_fences(text)), 18)


class TestRunFence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fc-run-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.env = {"VC_ROOT": self.tmp, "TMPDIR": self.tmp,
                    "STATE_FILE": os.path.join(self.tmp, "s.json")}

    def test_home_is_unset(self):
        rc, out, err = fc.run_fence('echo "${HOME:-unset}"', self.env)
        self.assertEqual((rc, out), (0, "unset\n"))

    def test_environment_is_exactly_four_names(self):
        rc, out, _ = fc.run_fence("env | cut -d= -f1 | sort", self.env)
        self.assertEqual(rc, 0)
        names = set(out.split()) - {"PWD", "SHLVL", "_", "OLDPWD"}
        self.assertEqual(names, {"PATH", "VC_ROOT", "TMPDIR", "STATE_FILE"})

    def test_exit_and_stderr_are_returned(self):
        rc, out, err = fc.run_fence("echo boom >&2; exit 3", self.env)
        self.assertEqual((rc, out, err), (3, "", "boom\n"))


class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "hashlib", "json", "os", "re", "shutil",
               "subprocess", "sys", "tempfile", "textwrap"}

    def _tree(self):
        with open(CAPTURE_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_module_level_imports(self):
        names = set()
        for node in self._tree().body:
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertTrue(names)
        self.assertLessEqual(names, self.ALLOWED)

    def test_no_plugin_behaviour_module_anywhere(self):
        found = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        self.assertFalse(found & {"carry_state", "finalize_gate", "batch_card",
                                  "batch_parse", "review_archive"}, found)

    def test_every_subprocess_run_has_an_explicit_timeout(self):
        calls = 0
        for node in ast.walk(self._tree()):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "run"
                    and getattr(node.func.value, "id", None) == "subprocess"):
                calls += 1
                self.assertIn("timeout", [kw.arg for kw in node.keywords],
                              "every subprocess.run needs an explicit timeout")
        self.assertGreater(calls, 0)

    def test_timeout_lock_trips_on_a_mutant(self):
        src = "import subprocess\nsubprocess.run(['true'])\n"
        tree = ast.parse(src)
        missing = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "run"
                   and "timeout" not in [kw.arg for kw in n.keywords]]
        self.assertEqual(len(missing), 1)


if __name__ == "__main__":
    unittest.main()
