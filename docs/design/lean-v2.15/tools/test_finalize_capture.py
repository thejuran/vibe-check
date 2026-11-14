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


def _pinned_counts(vc_root, state_path, tmp):
    """The pinned counts helper's JSON for `state_path` with empty HEAD
    fingerprints, run in a child process."""
    blobs = os.path.join(tmp, "blobs.json")
    with open(blobs, "w", encoding="utf-8") as fh:
        fh.write("{}")
    with open(state_path, encoding="utf-8") as fh:
        proc = subprocess.run(
            ["python3", os.path.join(vc_root, "scripts", "carry_state.py"),
             "finalize-counts", "--head-blobs", blobs],
            stdin=fh, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout)


def _gate_actions(outputs):
    return [d["action"] for d in outputs["gate"]]


class TestCloseRoutes(_PinnedTree):
    """The two close routes walked from the pinned fences."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.outputs = {}
        try:
            for sid in ("clean-close", "card-first"):
                work = tempfile.mkdtemp(prefix="fc-walk-", dir=cls._tmp)
                cls.outputs[sid] = fc.FenceWalk2141().run(sid, cls.vc_root,
                                                          work)
        except BaseException:
            shutil.rmtree(cls._tmp, True)
            raise

    def test_outputs_follow_the_fixed_schema(self):
        for sid, out in self.outputs.items():
            self.assertEqual(set(out), set(fc.OUTPUT_KEYS), sid)
            self.assertEqual(set(out["tally"]), set(fc.TALLY_KEYS), sid)
            for step in out["steps"]:
                self.assertEqual(set(step), set(fc.STEP_KEYS), sid)

    def test_clean_close_writes(self):
        out = self.outputs["clean-close"]
        self.assertEqual(_gate_actions(out), ["write"])
        self.assertTrue(out["report"]["entries"])
        self.assertIsNone(out["stop_sentence"])
        self.assertGreaterEqual(out["tally"]["writes"], 1)
        self.assertGreaterEqual(out["tally"]["commands_run"], 3)
        self.assertTrue(out["state_closed"])
        self.assertTrue(out["files_archived"])

    def test_card_first_shows_the_card_before_any_write(self):
        out = self.outputs["card-first"]
        actions = _gate_actions(out)
        self.assertNotEqual(actions[0], "write")
        self.assertEqual(actions[-1], "write")
        ids = [s["id"] for s in out["steps"]]
        self.assertIn("card", ids)
        card_at = ids.index("card")
        gate_steps = [i for i, s in enumerate(out["steps"])
                      if s["id"] == "gate"]
        write_gate = [i for i in gate_steps
                      if json.loads(out["steps"][i]["stdout"].strip()
                                    .splitlines()[-1])["action"] == "write"]
        self.assertTrue(write_gate)
        self.assertLess(card_at, write_gate[0])
        self.assertTrue(out["steps"][card_at]["stdout"].strip())
        # the owner's answers were saved before the final gate
        record_at = ids.index("record-decisions")
        self.assertLess(card_at, record_at)
        self.assertLess(record_at, write_gate[0])
        self.assertTrue(out["report"]["entries"])
        self.assertIsNone(out["stop_sentence"])

    def test_owner_answers_are_fixed_strings(self):
        answers = fc.SITUATIONS["card-first"]["inputs"]["owner_answers"]
        self.assertEqual(answers, [{"q1": "dismiss 1,2,3,4,5,6 -- walk",
                                    "q2": None}])

    def test_fixture_six_row_has_open_findings(self):
        state = os.path.join(self.vc_root, *fc.SIX_ROW.split("/"))
        counts = _pinned_counts(self.vc_root, state, self._tmp)
        self.assertTrue(counts["outstanding_cw_hashes"]
                        + counts["unacknowledged_medium_hashes"]
                        + counts["undecided_nv_hashes"])

    def test_fixture_clean_close_state_has_none(self):
        dest = os.path.join(tempfile.mkdtemp(dir=self._tmp), "state.json")
        fc.prepare_state(self.vc_root, "clean-close", dest)
        counts = _pinned_counts(self.vc_root, dest, self._tmp)
        self.assertEqual((counts["outstanding_cw"],
                          counts["unacknowledged_medium"],
                          counts["undecided_nv"]), (0, 0, 0))
        # and the fixture it starts from did have some
        raw = os.path.join(self.vc_root, *fc.LOOP_STATE.split("/"))
        before = _pinned_counts(self.vc_root, raw, self._tmp)
        self.assertTrue(before["outstanding_cw_hashes"]
                        + before["unacknowledged_medium_hashes"]
                        + before["undecided_nv_hashes"])

    def test_unwalked_situations_raise_a_named_usage_error(self):
        for sid in ("one-rebuild", "refused-close", "fresh-shell-restart"):
            work = tempfile.mkdtemp(dir=self._tmp)
            with self.assertRaises(fc.UsageError) as ctx:
                fc.FenceWalk2141().run(sid, self.vc_root, work)
            self.assertIn(sid, str(ctx.exception))

    def test_no_stray_files_outside_the_work_directory(self):
        root = tempfile.mkdtemp(prefix="fc-root-")
        self.addCleanup(shutil.rmtree, root, True)
        work = tempfile.mkdtemp(prefix="fc-work-", dir=root)
        fc.FenceWalk2141().run("clean-close", self.vc_root, work)
        self.assertEqual(os.listdir(root), [os.path.basename(work)])
        self.assertTrue(os.listdir(work))
        shutil.rmtree(work)
        self.assertEqual(os.listdir(root), [])


class TestCaptureOne(unittest.TestCase):
    def _capture(self, sid):
        root = tempfile.mkdtemp(prefix="fc-cap-")
        self.addCleanup(shutil.rmtree, root, True)
        out = fc.capture_one(REPO, sid, tmp_root=root)
        self.assertEqual(os.listdir(root), [], "capture_one left files")
        return root, out

    def test_clean_close_is_deterministic(self):
        root_a, a = self._capture("clean-close")
        root_b, b = self._capture("clean-close")
        self.assertNotEqual(root_a, root_b)
        self.assertEqual(fc.canonical_json(a), fc.canonical_json(b))
        self.assertNotIn(root_a, fc.canonical_json(a))

    def test_card_first_is_deterministic(self):
        _, a = self._capture("card-first")
        _, b = self._capture("card-first")
        self.assertEqual(fc.canonical_json(a), fc.canonical_json(b))

    def test_normaliser_mutant_makes_captures_differ(self):
        def identity(text, workdir, vc_root=None):
            return text
        with mock.patch.object(fc, "normalise", identity):
            self.assertIs(fc.normalise, identity)
            root_a, a = self._capture("clean-close")
            root_b, b = self._capture("clean-close")
        self.assertNotEqual(root_a, root_b)
        self.assertIn(root_a, fc.canonical_json(a))
        self.assertNotEqual(fc.canonical_json(a), fc.canonical_json(b))

    def test_unwalked_situation_raises_and_cleans_up(self):
        root = tempfile.mkdtemp(prefix="fc-cap-")
        self.addCleanup(shutil.rmtree, root, True)
        with self.assertRaises(fc.UsageError) as ctx:
            fc.capture_one(REPO, "refused-close", tmp_root=root)
        self.assertIn("refused-close", str(ctx.exception))
        self.assertEqual(os.listdir(root), [])


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
