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

    def test_unknown_situation_or_leg_raises_a_named_usage_error(self):
        work = tempfile.mkdtemp(dir=self._tmp)
        with self.assertRaises(fc.UsageError) as ctx:
            fc.FenceWalk2141().run("no-such-situation", self.vc_root, work)
        self.assertIn("no-such-situation", str(ctx.exception))
        with self.assertRaises(fc.UsageError) as ctx:
            fc.FenceWalk2141().run("clean-close", self.vc_root, work,
                                   leg="no-such-leg")
        self.assertIn("no-such-leg", str(ctx.exception))

    def test_scratch_files_are_not_counted_as_written(self):
        """The mktemp files the fences make are scratch, not Finalize's
        writes: only the report counts on the clean route."""
        self.assertEqual(self.outputs["clean-close"]["files_written"],
                         [".turingmind/REVIEW.md"])
        self.assertTrue(any("/" + fc.SCRATCH_DIR + "/vc." in s["stdout"]
                            for s in self.outputs["clean-close"]["steps"]))

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

    def test_failing_driver_raises_and_cleans_up(self):
        class Refuses:
            def run(self, situation_id, vc_root, workdir, leg=None):
                with open(os.path.join(workdir, "partial"), "w") as fh:
                    fh.write("x")
                raise fc.UsageError("refuses %s" % situation_id)
        root = tempfile.mkdtemp(prefix="fc-cap-")
        self.addCleanup(shutil.rmtree, root, True)
        with self.assertRaises(fc.UsageError) as ctx:
            fc.capture_one(REPO, "refused-close", driver=Refuses(),
                           tmp_root=root)
        self.assertIn("refused-close", str(ctx.exception))
        self.assertEqual(os.listdir(root), [])


# --------------------------------------------------------------------------- #
# The rebuild, refusal and restart situations
# --------------------------------------------------------------------------- #
ARCH_HASH = ("22d360d9c3d841748413b88d41e0840f"
             "d0898a854ee6fa5188f134846a8c7449")
ARCH_FILE = "src/utils/integrationDeadline.ts"


def _steps(out, step_id):
    return [s for s in out["steps"] if s["id"] == step_id]


def _minted(out, step_id, name):
    """The paths printed after `NAME=` by every `step_id` step, in order."""
    return [dict(re.findall(r"^([A-Z_]+FILE)=(.+)$", s["stdout"], re.M))[name]
            for s in _steps(out, step_id)]


def one_rebuild_problems(out):
    """What is wrong with a raw (un-normalised) one-rebuild main leg: the
    first counts step fails on the missing path, exactly one rebuild into a
    NEW BLOBFILE follows, the gate decides `write` on a GATEFILE minted after
    the rebuild, and the report is read."""
    problems = []
    counts = _steps(out, "counts")
    if not counts or counts[0]["exit"] == 0 or counts[0]["stdout"] != "":
        problems.append("the first counts step did not fail silently")
    blobs = _minted(out, "blobfile", "BLOBFILE")
    if len(blobs) != 2:
        problems.append("%d BLOBFILE mints, not 2 (one rebuild)" % len(blobs))
    elif blobs[0] == blobs[1]:
        problems.append("the rebuild reused the first BLOBFILE")
    if len(counts) != 2 or counts[-1]["exit"] != 0:
        problems.append("the rebuilt counts step did not succeed")
    if _gate_actions(out) != ["write"]:
        problems.append("gate decisions %r, not ['write']"
                        % _gate_actions(out))
    if out["stop_sentence"] is not None:
        problems.append("stopped: %r" % out["stop_sentence"])
    if not (out["report"] or {}).get("entries"):
        problems.append("no report entries")
    return problems


def stopped_problems(out, sentence):
    """What is wrong with a raw leg that must stop with `sentence`, having
    written nothing, archived nothing and left the state live."""
    problems = []
    if out["stop_sentence"] != sentence:
        problems.append("stop sentence %r" % (out["stop_sentence"],))
    for key in ("files_written", "files_archived"):
        if out[key]:
            problems.append("%s: %r" % (key, out[key]))
    if out["state_closed"]:
        problems.append("state closed")
    if out["report"] is not None:
        problems.append("a report was read for the owner")
    return problems


class TestFailureRoutes(_PinnedTree):
    """one-rebuild, refused-close and fresh-shell-restart, walked raw from
    the pinned fences (paths not normalised, so mints can be compared)."""

    RUNS = (("one-rebuild", None), ("one-rebuild", "second-failure"),
            ("refused-close", None), ("refused-close", "unarchivable-report"),
            ("fresh-shell-restart", None))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.outputs, cls.work = {}, {}
        try:
            cls.stop = fc.stop_sentence(cls.finalize_text)
            for sid, leg in cls.RUNS:
                work = tempfile.mkdtemp(prefix="fc-walk-", dir=cls._tmp)
                cls.work[(sid, leg)] = work
                cls.outputs[(sid, leg)] = fc.FenceWalk2141().run(
                    sid, cls.vc_root, work, leg=leg)
        except BaseException:
            shutil.rmtree(cls._tmp, True)
            raise

    # -- fixtures ------------------------------------------------------------
    def test_stop_sentence_is_read_from_the_pinned_file(self):
        self.assertTrue(self.stop.strip())
        self.assertTrue(self.stop.startswith("Finalize stopped"))
        self.assertIn('The stop is exactly one sentence: "%s"' % self.stop,
                      self.finalize_text)
        pinned = _git_show_bytes(FINALIZE_REL).decode("utf-8")
        self.assertIn(self.stop, pinned)

    def test_archive_fence_is_the_four_backtick_fence(self):
        four = re.findall(r"````bash\n(.*?)\n````", self.finalize_text, re.S)
        self.assertEqual(len(four), 1)
        used = fc.fence_holding(fc.extract_fences(self.finalize_text),
                                fc.PRIOR_REVIEW_CALL)
        self.assertEqual(used, four[0])

    def test_legs_are_declared(self):
        self.assertEqual(sorted(fc.SITUATIONS["one-rebuild"]["legs"]),
                         ["second-failure"])
        self.assertEqual(sorted(fc.SITUATIONS["refused-close"]["legs"]),
                         ["unarchivable-report"])
        for sid in ("clean-close", "card-first", "fresh-shell-restart"):
            self.assertEqual(dict(fc.SITUATIONS[sid].get("legs", {})), {},
                             sid)

    def test_restart_fixture_has_the_arch_finding_and_no_verdict(self):
        with open(os.path.join(self.vc_root, *fc.SIX_ROW.split("/")),
                  encoding="utf-8") as fh:
            state = json.load(fh)
        arch = [f for p in state["passes"] for f in p.get("findings", [])
                if f.get("stable_hash") == ARCH_HASH]
        self.assertEqual([(f["band"], f["file"]) for f in arch],
                         [("critical", ARCH_FILE)])
        self.assertNotIn("fix_verdicts", state)
        inputs = fc.SITUATIONS["fresh-shell-restart"]["inputs"]
        self.assertEqual(sorted(inputs["fix_verdicts"]), [ARCH_HASH])
        self.assertEqual(inputs["head_blobs"],
                         {ARCH_FILE: inputs["fix_verdicts"][ARCH_HASH]
                          ["verified_blob"]})

    # -- one-rebuild --------------------------------------------------------
    def test_one_rebuild_takes_exactly_one_rebuild_and_writes(self):
        self.assertEqual(one_rebuild_problems(
            self.outputs[("one-rebuild", None)]), [])

    def test_one_rebuild_first_counts_failure_shows_stderr_only(self):
        first = _steps(self.outputs[("one-rebuild", None)], "counts")[0]
        self.assertTrue(first["stderr_present"])

    def test_one_rebuild_gate_decides_on_a_gatefile_minted_after_rebuild(self):
        out = self.outputs[("one-rebuild", None)]
        ids = [s["id"] for s in out["steps"]]
        blob_at = [i for i, x in enumerate(ids) if x == "blobfile"]
        gate_at = [i for i, x in enumerate(ids) if x == "gatefile"]
        self.assertEqual(len(gate_at), 1)
        self.assertGreater(gate_at[0], blob_at[1])

    def test_second_failure_stops_with_the_stop_sentence(self):
        out = self.outputs[("one-rebuild", "second-failure")]
        self.assertEqual(stopped_problems(out, self.stop), [])
        self.assertEqual(len(_steps(out, "blobfile")), 2)
        self.assertEqual(out["gate"], [])
        self.assertTrue(all(s["exit"] != 0 for s in _steps(out, "counts")))

    # -- refused-close ------------------------------------------------------
    def test_refused_close_shows_only_the_stop_sentence(self):
        out = self.outputs[("refused-close", None)]
        self.assertEqual(stopped_problems(out, self.stop), [])
        self.assertEqual(out["gate"], [])
        gates = _steps(out, "gate")
        self.assertEqual(len(gates), 2)
        for step in gates:
            self.assertEqual((step["exit"], step["stdout"]), (1, ""))
            self.assertTrue(step["stderr_present"])
        files = _minted(out, "gatefile", "GATEFILE")
        self.assertEqual(len(files), 2)
        self.assertNotEqual(files[0], files[1])
        for path in files:
            with open(path + ".err", encoding="utf-8") as fh:
                self.assertIn("Traceback", fh.read())
        self.assertFalse(os.path.exists(os.path.join(
            self.work[("refused-close", None)], ".turingmind", "REVIEW.md")))

    def test_refused_close_leaves_the_state_live(self):
        work = self.work[("refused-close", None)]
        self.assertTrue(os.path.isfile(os.path.join(
            work, *fc.STATE_REL.split("/"))))

    def test_unarchivable_report_stops_and_archives_nothing(self):
        out = self.outputs[("refused-close", "unarchivable-report")]
        self.assertTrue(out["stop_sentence"])
        self.assertTrue(out["stop_sentence"].startswith(
            "Finalize stopped — the earlier REVIEW.md could not be archived"))
        self.assertIn(out["stop_sentence"], self.finalize_text)
        self.assertEqual(stopped_problems(out, out["stop_sentence"]), [])
        self.assertEqual(_gate_actions(out), ["write"])
        self.assertNotEqual(_steps(out, "prior-review-archive")[0]["exit"], 0)
        self.assertEqual(_steps(out, "archive-state"), [])
        work = self.work[("refused-close", "unarchivable-report")]
        tm = os.path.join(work, ".turingmind")
        with open(os.path.join(tm, "REVIEW.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), fc.SITUATIONS["refused-close"]
                             ["legs"]["unarchivable-report"]["prior_review_md"])
        self.assertEqual(sorted(os.listdir(tm)), ["REVIEW.md", "state"])
        # the driver gave the directory its permissions back
        self.assertTrue(os.access(tm, os.W_OK))

    def test_unarchivable_report_as_root_is_a_named_usage_error(self):
        work = tempfile.mkdtemp(prefix="fc-root-", dir=self._tmp)
        with mock.patch.object(fc.os, "geteuid", return_value=0):
            self.assertEqual(fc.os.geteuid(), 0)
            with self.assertRaises(fc.UsageError) as ctx:
                fc.FenceWalk2141().run("refused-close", self.vc_root, work,
                                       leg="unarchivable-report")
        self.assertIn("root", str(ctx.exception))

    # -- fresh-shell-restart ------------------------------------------------
    def test_restart_decides_on_new_gatefile_and_blobfile(self):
        out = self.outputs[("fresh-shell-restart", None)]
        self.assertEqual(_gate_actions(out),
                         ["outstanding-to-phase-5", "write"])
        blobs = _minted(out, "blobfile", "BLOBFILE")
        gates = _minted(out, "gatefile", "GATEFILE")
        self.assertEqual(len(blobs), 2)
        self.assertEqual(len(gates), 2)
        self.assertNotEqual(blobs[0], blobs[1])
        self.assertNotEqual(gates[0], gates[1])
        ids = [s["id"] for s in out["steps"]]
        record_at = ids.index("record-decisions")
        second_blob = [i for i, x in enumerate(ids) if x == "blobfile"][1]
        second_gate = [i for i, x in enumerate(ids) if x == "gatefile"][1]
        last_gate = [i for i, x in enumerate(ids) if x == "gate"][-1]
        self.assertLess(record_at, second_blob)
        self.assertLess(second_blob, second_gate)
        self.assertLess(second_gate, last_gate)
        self.assertTrue(out["report"]["entries"])
        self.assertIsNone(out["stop_sentence"])
        self.assertTrue(out["state_closed"])

    def test_restart_honours_the_verdict_on_each_fresh_fingerprint(self):
        out = self.outputs[("fresh-shell-restart", None)]
        counts = [json.loads(s["stdout"].strip().splitlines()[0])
                  for s in _steps(out, "counts")]
        self.assertEqual(len(counts), 2)
        self.assertEqual([(c["outstanding_cw"], c["unacknowledged_medium"],
                           c["undecided_nv"]) for c in counts],
                         [(4, 1, 0), (0, 0, 0)])
        for c in counts:
            self.assertEqual(c["verified_obsolete_hashes"], [ARCH_HASH])

    def test_restart_answer_names_every_card_row(self):
        answer = fc.SITUATIONS["fresh-shell-restart"]["inputs"][
            "owner_answers"][0]["q1"]
        self.assertEqual(answer.split()[1],
                         ",".join(str(n) for n in range(1, 6)))

    # -- driver mutants -----------------------------------------------------
    def test_mutant_no_rebuild_changes_one_rebuild(self):
        self.assertEqual(fc.FenceWalk2141.REBUILDS, 1)
        work = tempfile.mkdtemp(prefix="fc-mut-", dir=self._tmp)
        with mock.patch.object(fc.FenceWalk2141, "REBUILDS", 0):
            self.assertEqual(fc.FenceWalk2141.REBUILDS, 0)
            mutant = fc.FenceWalk2141().run("one-rebuild", self.vc_root, work)
        self.assertNotEqual(one_rebuild_problems(mutant), [])
        real = self.outputs[("one-rebuild", None)]
        self.assertNotEqual(
            fc.canonical_json(fc.normalise_outputs(mutant, work, self.vc_root)),
            fc.canonical_json(fc.normalise_outputs(
                real, self.work[("one-rebuild", None)], self.vc_root)))

    def test_mutant_report_after_malformed_gate_is_caught(self):
        real_stop = fc._Walk.stop

        def stop_then_write(walk, sentence):
            real_stop(walk, sentence)
            walk.write(os.path.join(walk.workdir,
                                    *fc.REVIEW_REL.split("/")), "report\n")
        work = tempfile.mkdtemp(prefix="fc-mut-", dir=self._tmp)
        with mock.patch.object(fc._Walk, "stop", stop_then_write):
            self.assertIs(fc._Walk.stop, stop_then_write)
            mutant = fc.FenceWalk2141().run("refused-close", self.vc_root,
                                            work)
        self.assertEqual(mutant["files_written"], [fc.REVIEW_REL])
        self.assertNotEqual(stopped_problems(mutant, self.stop), [])


class TestFailureRoutesDeterministic(unittest.TestCase):
    def test_each_situation_captured_twice_is_equal(self):
        for sid in ("one-rebuild", "refused-close", "fresh-shell-restart"):
            with self.subTest(sid):
                roots = []
                got = []
                for _ in range(2):
                    root = tempfile.mkdtemp(prefix="fc-det-")
                    self.addCleanup(shutil.rmtree, root, True)
                    roots.append(root)
                    got.append(fc.capture_situation(REPO, sid, tmp_root=root))
                    self.assertEqual(os.listdir(root), [])
                self.assertNotEqual(roots[0], roots[1])
                self.assertEqual(set(got[0]),
                                 set(fc.OUTPUT_KEYS) | {"legs"})
                self.assertEqual(sorted(got[0]["legs"]),
                                 sorted(fc.SITUATIONS[sid].get("legs", {})))
                self.assertEqual(fc.canonical_json(got[0]),
                                 fc.canonical_json(got[1]))

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
