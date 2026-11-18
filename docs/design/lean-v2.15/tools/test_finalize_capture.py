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

# --------------------------------------------------------------------------- #
# The committed five-situation record
# --------------------------------------------------------------------------- #
RECORD = os.path.join(REPO, "docs", "design", "lean-v2.15", "baseline",
                      "finalize-situations-v2.14.1.json")
PLANTS = ("/Users/x/work", "/home/runner/work", "/private/tmp/vc.abc")


def _read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _planted(text, plant):
    """The committed record's text with `plant` added to one recorded
    stdout."""
    record = json.loads(text)
    record["situations"]["clean-close"]["steps"][0]["stdout"] += " " + plant
    return fc.record_text(record)


def assert_plant_reported(case, text, plant):
    """The planted-path break test: the plant is really in the text, and
    the machine-path lock reports it."""
    mutant = _planted(text, plant)
    case.assertNotEqual(mutant, text)
    case.assertIn(plant, mutant)
    case.assertNotIn(plant, text)
    problems = fc.machine_path_problems(mutant)
    case.assertTrue(problems, "the lock missed %s" % plant)
    head = "/" + plant.split("/")[1] + "/"
    case.assertTrue(any(head in p for p in problems), problems)


class TestRecord(unittest.TestCase):
    """The committed record re-derives exactly, and any change is named."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read_text(RECORD)
        cls.record = json.loads(cls.text)
        cls.fresh = fc.capture(REPO)

    def _tampered(self, mutate):
        """verify() on a temp copy of the committed record changed by
        `mutate`; asserts the copy really differs."""
        record = json.loads(self.text)
        mutate(record)
        text = fc.record_text(record)
        self.assertNotEqual(text, self.text)
        tmp = tempfile.mkdtemp(prefix="fc-tamper-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "record.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return fc.verify(REPO, path, fresh=self.fresh)

    # -- shape --------------------------------------------------------------
    def test_record_shape(self):
        self.assertEqual(list(self.record["situations"]), SITUATION_IDS)
        self.assertEqual(self.record["baseline_commit"], fc.BASELINE_COMMIT)
        self.assertEqual(self.record["baseline_commit"],
                         "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4")
        self.assertEqual(self.record["driver"], "fence-walk-2.14.1")
        self.assertEqual(self.record["schema"], fc.SCHEMA)
        self.assertEqual(self.record["normalisation"],
                         list(fc.NORMALISATION))
        self.assertEqual(self.record["sha256"],
                         fc.canonical_sha256(self.record["situations"]))
        for sid, out in self.record["situations"].items():
            self.assertEqual(set(out), set(fc.OUTPUT_KEYS) | {"legs"}, sid)

    def test_sidecar_holds_the_same_fingerprint(self):
        self.assertEqual(_read_text(RECORD + ".sha256"),
                         self.record["sha256"] + "\n")

    def test_record_text_is_written_as_capture_writes_it(self):
        self.assertTrue(self.text.endswith("}\n"))
        self.assertEqual(fc.record_text(self.record), self.text)

    def test_situation_outcomes_in_the_record(self):
        sit = self.record["situations"]
        acts = {sid: [d["action"] for d in out["gate"]]
                for sid, out in sit.items()}
        self.assertEqual(acts["clean-close"], ["write"])
        self.assertEqual(acts["card-first"][-1], "write")
        self.assertEqual(acts["one-rebuild"], ["write"])
        self.assertEqual(acts["refused-close"], [])
        self.assertEqual(acts["fresh-shell-restart"],
                         ["outstanding-to-phase-5", "write"])
        stop = sit["refused-close"]["stop_sentence"]
        self.assertTrue(stop.startswith("Finalize stopped"))
        self.assertEqual(sit["one-rebuild"]["legs"]["second-failure"]
                         ["stop_sentence"], stop)
        for out in (sit["refused-close"],
                    sit["refused-close"]["legs"]["unarchivable-report"]):
            self.assertEqual((out["files_written"], out["files_archived"],
                              out["state_closed"]), ([], [], False))

    # -- re-derivation ------------------------------------------------------
    def test_capture_twice_gives_equal_records(self):
        roots = [tempfile.mkdtemp(prefix="fc-rec-") for _ in range(2)]
        for root in roots:
            self.addCleanup(shutil.rmtree, root, True)
        a, b = (fc.capture(REPO, tmp_root=root) for root in roots)
        self.assertEqual(fc.record_text(a), fc.record_text(b))
        self.assertEqual(a["sha256"], b["sha256"])
        for root in roots:
            self.assertEqual(os.listdir(root), [])

    def test_fresh_capture_equals_the_committed_text(self):
        self.assertEqual(fc.record_text(self.fresh), self.text)

    def test_verify_committed_record_is_clean(self):
        self.assertEqual(fc.verify(REPO, RECORD), [])

    # -- tamper mutants -----------------------------------------------------
    def test_tamper_one_stdout_character_is_named(self):
        def mutate(record):
            step = record["situations"]["card-first"]["steps"][1]
            old = step["stdout"]
            step["stdout"] = old[:-2] + ("x" if old[-2] != "x" else "y") \
                + old[-1:]
            self.assertNotEqual(step["stdout"], old)
        problems = self._tampered(mutate)
        self.assertTrue(any(p.startswith("card-first") for p in problems),
                        problems)

    def test_tamper_gate_action_is_named(self):
        def mutate(record):
            gate = record["situations"]["one-rebuild"]["gate"][0]
            self.assertEqual(gate["action"], "write")
            gate["action"] = "fallback"
        problems = self._tampered(mutate)
        self.assertTrue(any(p.startswith("one-rebuild") for p in problems),
                        problems)

    def test_tamper_removed_situation_is_named(self):
        def mutate(record):
            del record["situations"]["fresh-shell-restart"]
            self.assertNotIn("fresh-shell-restart", record["situations"])
        problems = self._tampered(mutate)
        self.assertTrue(any(p.startswith("fresh-shell-restart")
                            for p in problems), problems)

    def test_tamper_stored_sha256_is_named(self):
        def mutate(record):
            old = record["sha256"]
            record["sha256"] = ("0" if old[0] != "0" else "1") + old[1:]
            self.assertNotEqual(record["sha256"], old)
        problems = self._tampered(mutate)
        self.assertTrue(any(p.startswith("sha256") for p in problems),
                        problems)
        self.assertFalse(any(p.startswith(tuple(SITUATION_IDS))
                             for p in problems), problems)

    def test_driver_mutant_is_named_against_the_record(self):
        self.assertEqual(fc.FenceWalk2141.REBUILDS, 1)
        with mock.patch.object(fc.FenceWalk2141, "REBUILDS", 0):
            self.assertEqual(fc.FenceWalk2141.REBUILDS, 0)
            problems = fc.verify(REPO, RECORD)
        self.assertTrue(any(p.startswith("one-rebuild") for p in problems),
                        problems)
        self.assertFalse(any(p.startswith("clean-close") for p in problems),
                         problems)

    # -- machine paths ------------------------------------------------------
    def test_record_holds_no_machine_paths(self):
        self.assertEqual(fc.machine_path_problems(self.text), [])

    def test_lock_names_each_pattern(self):
        for pattern in ("/Users/", "/private/", "/tmp/", "/home/"):
            with self.subTest(pattern):
                problems = fc.machine_path_problems("a %sb c" % pattern,
                                                    account="")
                self.assertEqual(len(problems), 1, problems)
                self.assertIn(pattern, problems[0])

    def test_lock_names_the_account(self):
        problems = fc.machine_path_problems("owner is someacct here",
                                            account="someacct")
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("account", problems[0])
        self.assertEqual(fc.machine_path_problems("owner is abc",
                                                  account="abc"), [])
        user = fc.current_account()
        if user and len(user) > 3:
            self.assertTrue(fc.machine_path_problems("x %s y" % user))

    def test_planted_users_path_is_reported(self):
        assert_plant_reported(self, self.text, PLANTS[0])

    def test_planted_home_path_is_reported(self):
        assert_plant_reported(self, self.text, PLANTS[1])

    def test_planted_private_tmp_path_is_reported(self):
        assert_plant_reported(self, self.text, PLANTS[2])

    # -- CLI ----------------------------------------------------------------
    def test_cli_verify_committed_exits_zero(self):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = fc.main(["verify", "--repo", REPO, "--record", RECORD])
        self.assertEqual(rc, 0, out.getvalue())

    def test_cli_verify_tampered_copy_exits_one(self):
        tmp = tempfile.mkdtemp(prefix="fc-cli-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "record.json")
        mutant = _planted(self.text, PLANTS[0])
        self.assertIn(PLANTS[0], mutant)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(mutant)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = fc.main(["verify", "--repo", REPO, "--record", path])
        self.assertEqual(rc, 1)
        shown = out.getvalue() + err.getvalue()
        self.assertIn("FINALIZE BASELINE DIFFERS — STOPPING", shown)
        self.assertIn("clean-close", shown)

    def test_cli_verify_unreadable_record_exits_two(self):
        tmp = tempfile.mkdtemp(prefix="fc-cli-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "record.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("not json")
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = fc.main(["verify", "--repo", REPO, "--record", path])
        self.assertEqual(rc, 2)

    def test_cli_capture_refuses_a_record_with_a_machine_path(self):
        planted = json.loads(_planted(self.text, PLANTS[0]))
        tmp = tempfile.mkdtemp(prefix="fc-cli-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "record.json")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(fc, "capture", return_value=planted):
            with redirect_stdout(out), redirect_stderr(err):
                rc = fc.main(["capture", "--repo", REPO, "--out", path])
        self.assertEqual(rc, 1)
        self.assertIn("RECORD HOLDS A MACHINE PATH — STOPPING",
                      out.getvalue() + err.getvalue())
        self.assertEqual(os.listdir(tmp), [])


class TestMutants(unittest.TestCase):
    """The machine-path lock is the thing the planted-path tests test."""

    def test_patched_off_lock_misses_the_plant(self):
        text = _read_text(RECORD)
        assert_plant_reported(self, text, PLANTS[0])

        def never(text, account=None):
            return []
        with mock.patch.object(fc, "machine_path_problems", never):
            self.assertIs(fc.machine_path_problems, never)
            for plant in PLANTS:
                with self.subTest(plant):
                    with self.assertRaises(AssertionError):
                        assert_plant_reported(self, text, plant)

class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "getpass", "hashlib", "json", "os", "re",
               "shutil", "subprocess", "sys", "tempfile", "textwrap"}

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


# --------------------------------------------------------------------------- #
# The helper driver: the same five situations on the new instructions
# --------------------------------------------------------------------------- #
LIVE_PLUGIN = os.path.join(REPO, "plugins", "vibe-check")
COUNTS_HALT = ("I'm uncertain about Finalize mode — carry_state.py failed; "
               "nothing was written or archived.")
REPORT_HALT = ("I'm uncertain about Finalize mode — batch_card.py "
               "decisions-report failed; nothing was written or archived.")
HELPER_RUNS = (("clean-close", None), ("card-first", None),
               ("one-rebuild", None), ("one-rebuild", "second-failure"),
               ("refused-close", None),
               ("refused-close", "unarchivable-report"),
               ("fresh-shell-restart", None))
EDIT_DURING_CARD = "// edited while the owner answered the card\n"


def _copy_live_plugin(dest):
    """A copy of the working tree's plugins/vibe-check under `dest`; returns
    the plugin root inside it."""
    root = os.path.join(dest, "plugins", "vibe-check")
    shutil.copytree(LIVE_PLUGIN, root,
                    ignore=shutil.ignore_patterns("__pycache__"))
    return root


def _record():
    with open(RECORD, encoding="utf-8") as fh:
        return json.load(fh)


def _recorded(record, sid, leg=None):
    out = record["situations"][sid]
    return out["legs"][leg] if leg else out


def _outcome_differences(want, got):
    return [p for key in fc.OUTCOME_KEYS
            for p in fc._differences(want[key], got[key], key)]


def _inputs_steps(out):
    return _steps(out, "finalize-inputs")


def edit_during_card(driver, vc_root, work):
    """fresh-shell-restart with the verdict's file edited while the owner
    answers the card: the re-run after the answer must see the edit (the
    critical reopens), never close it on the pre-card fingerprints. Returns
    (the decision after the answer or None, the walk)."""
    walk, inputs = driver.prepare("fresh-shell-restart", vc_root, work)
    blob, decision = driver.gated(walk, inputs)
    if decision is None or decision["action"] != "outstanding-to-phase-5":
        raise AssertionError("no card before the edit: %r" % (decision,))
    walk.card(blob, inputs["owner_answers"][0])
    with open(os.path.join(work, *ARCH_FILE.split("/")), "a",
              encoding="utf-8") as fh:
        fh.write(EDIT_DURING_CARD)
    _, after = driver.gated(walk, inputs)
    return after, walk


class _CandidateTree(unittest.TestCase):
    """One copy of the live plugins/vibe-check for the whole class."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="fc-cand-")
        try:
            cls.vc_root = _copy_live_plugin(cls._tmp)
            with open(os.path.join(cls.vc_root, "phases", "shared",
                                   "90-finalize.md"), encoding="utf-8") as fh:
                cls.finalize_text = fh.read()
            cls.record = _record()
        except BaseException:
            shutil.rmtree(cls._tmp, True)
            raise

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, True)

    def _work(self):
        return tempfile.mkdtemp(prefix="fc-hw-", dir=self._tmp)


class TestHelperWalk(_CandidateTree):
    """The five situations and both legs walked raw on the new instructions
    (paths not normalised, so mints can be compared)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.outputs, cls.work, cls.walks = {}, {}, {}
        try:
            cls.stop = fc.stop_sentence(cls.finalize_text)
            for sid, leg in HELPER_RUNS:
                work = tempfile.mkdtemp(prefix="fc-hw-", dir=cls._tmp)
                driver = fc.HelperWalk()
                cls.work[(sid, leg)] = work
                cls.outputs[(sid, leg)] = driver.run(sid, cls.vc_root, work,
                                                     leg=leg)
                cls.walks[(sid, leg)] = driver.last_walk
        except BaseException:
            shutil.rmtree(cls._tmp, True)
            raise

    def _normalised(self, key):
        return fc.normalise_outputs(self.outputs[key], self.work[key],
                                    self.vc_root)

    # -- the needle and the names ---------------------------------------------
    def test_driver_identity(self):
        self.assertTrue(issubclass(fc.HelperWalk, fc.FenceWalk2141))
        self.assertEqual(fc.HelperWalk.NAME, "helper-walk-2.15")
        self.assertEqual(fc.HelperWalk.REBUILDS, 1)
        self.assertIs(fc.DRIVERS[fc.BASELINE_COMMIT], fc.FenceWalk2141)
        self.assertEqual(fc.OUTCOME_KEYS,
                         ("gate", "stop_sentence", "report", "files_written",
                          "files_archived", "state_closed"))
        self.assertLessEqual(set(fc.OUTCOME_KEYS), set(fc.OUTPUT_KEYS))

    def test_the_needle_finds_exactly_one_fence(self):
        fences = fc.extract_fences(self.finalize_text)
        self.assertEqual(sum(fc.FINALIZE_INPUTS_CALL in f for f in fences), 1)
        self.assertIn(BLOB_PRINT, fc.fence_holding(fences,
                                                   fc.FINALIZE_INPUTS_CALL))

    # -- outcome fields ------------------------------------------------------
    def test_outcome_fields_equal_the_record(self):
        for sid, leg in HELPER_RUNS:
            with self.subTest(sid, leg=leg):
                got = self._normalised((sid, leg))
                want = _recorded(self.record, sid, leg)
                self.assertEqual(_outcome_differences(want, got), [])

    def test_outputs_follow_the_fixed_schema(self):
        for key, out in self.outputs.items():
            self.assertEqual(set(out), set(fc.OUTPUT_KEYS), key)
            self.assertEqual(set(out["tally"]), set(fc.TALLY_KEYS), key)
            for step in out["steps"]:
                self.assertEqual(set(step), set(fc.STEP_KEYS), key)

    def test_fewer_commands_than_the_record(self):
        got = self.outputs[("clean-close", None)]["tally"]["commands_run"]
        want = _recorded(self.record, "clean-close")["tally"]["commands_run"]
        self.assertLess(got, want)

    # -- the rebuild ---------------------------------------------------------
    def test_one_rebuild_fails_once_then_writes(self):
        out = self.outputs[("one-rebuild", None)]
        steps = _inputs_steps(out)
        self.assertEqual([s["exit"] for s in steps][:1], [1])
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[1]["exit"], 0)
        blobs = _minted(out, "finalize-inputs", "BLOBFILE")
        self.assertEqual(len(set(blobs)), 2, blobs)
        self.assertEqual(_gate_actions(out), ["write"])
        self.assertIsNone(out["stop_sentence"])

    def test_second_failure_stops_with_nothing_written(self):
        out = self.outputs[("one-rebuild", "second-failure")]
        self.assertEqual([s["exit"] for s in _inputs_steps(out)], [1, 1])
        self.assertEqual(stopped_problems(out, self.stop), [])
        self.assertEqual(out["gate"], [])

    def test_refused_close_stops_after_two_faults(self):
        out = self.outputs[("refused-close", None)]
        self.assertEqual([s["exit"] for s in _inputs_steps(out)], [1, 1])
        self.assertEqual(stopped_problems(out, self.stop), [])
        self.assertEqual(out["gate"], [])

    def test_counting_line_on_every_failed_attempt(self):
        """D-18: a failed attempt shows the counting step's one line, then
        the fence's counting sentence, and nothing else; the text stays in
        memory and is not added to the record's step shape."""
        failed = 0
        for key in (("one-rebuild", None), ("one-rebuild", "second-failure"),
                    ("refused-close", None)):
            for rc, err in self.walks[key].attempt_stderr:
                if rc == 0:
                    continue
                failed += 1
                with self.subTest(key=key, n=failed):
                    lines = err.splitlines()
                    self.assertEqual(len(lines), 2, err)
                    self.assertEqual(lines[1], COUNTS_HALT)
                    self.assertTrue(lines[0].strip())
                    self.assertNotIn("Traceback", err)
                    self.assertTrue(err.endswith("\n"))
        self.assertEqual(failed, 5)
        self.assertEqual(fc.STEP_KEYS, ("id", "exit", "stdout",
                                        "stderr_present"))

    # -- the restart in a real git folder ------------------------------------
    def test_restart_is_prepared_in_a_real_git_folder_outside_the_walk(self):
        key = ("fresh-shell-restart", None)
        work, walk, out = self.work[key], self.walks[key], self.outputs[key]
        dot_git = os.path.join(work, ".git")
        self.assertTrue(os.path.isfile(dot_git))
        self.assertFalse(os.path.isdir(dot_git))
        self.assertTrue(os.path.isdir(walk.git_dir))
        rel = os.path.relpath(os.path.realpath(walk.git_dir),
                              os.path.realpath(work))
        self.assertTrue(rel.startswith(".."), rel)
        for name in ("files_written", "files_archived"):
            self.assertFalse([r for r in out[name] if r.startswith(".git")],
                             out[name])
        proc = subprocess.run(["git", "-C", work, "rev-parse",
                               "HEAD:" + ARCH_FILE], capture_output=True,
                              text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(walk.real_blobs, {ARCH_FILE: proc.stdout.strip()})
        self.assertNotEqual(proc.stdout.strip(), fc.ARCH_BLOB)

    def test_every_walk_runs_on_a_reviewed_tree(self):
        for key, walk in self.walks.items():
            work = self.work[key]
            self.assertTrue(walk.git_dir and os.path.isdir(walk.git_dir), key)
            want = fc.finding_files(self.vc_root,
                                    fc.situation_inputs(key[0], key[1]))
            self.assertTrue(want, key)
            proc = subprocess.run(["git", "-C", work, "ls-tree", "-r",
                                   "--name-only", "HEAD"],
                                  capture_output=True, text=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertLessEqual(set(want), set(proc.stdout.split()), key)

    def test_mutant_without_the_reviewed_tree_stamp_refuses(self):
        with mock.patch.object(fc, "stamp_reviewed_tree",
                               lambda *args: None):
            with self.assertRaises(fc.CaptureError) as caught:
                fc.HelperWalk().run("clean-close", self.vc_root,
                                    self._work())
        self.assertIn("stale", str(caught.exception))

    def test_restart_card_route_across_fresh_shells(self):
        key = ("fresh-shell-restart", None)
        out, walk = self.outputs[key], self.walks[key]
        self.assertEqual(_gate_actions(out), ["outstanding-to-phase-5",
                                              "write"])
        blobs = _minted(out, "finalize-inputs", "BLOBFILE")
        self.assertEqual(len(blobs), 2)
        self.assertNotEqual(blobs[0], blobs[1])
        for result in walk.results:
            self.assertEqual(result["counts"]["verified_obsolete_hashes"],
                             [ARCH_HASH])
        self.assertIn("card", [s["id"] for s in out["steps"]])

    # -- re-derivation --------------------------------------------------------
    def test_walked_twice_gives_the_same_normalised_outputs(self):
        for sid in ("one-rebuild", "fresh-shell-restart"):
            with self.subTest(sid):
                got = []
                for _ in range(2):
                    root = tempfile.mkdtemp(prefix="fc-hwdet-")
                    self.addCleanup(shutil.rmtree, root, True)
                    got.append(fc.capture_situation(
                        REPO, sid, driver="helper", tmp_root=root,
                        root=LIVE_PLUGIN))
                    self.assertEqual(os.listdir(root), [])
                self.assertEqual(fc.canonical_json(got[0]),
                                 fc.canonical_json(got[1]))

    # -- mutants ---------------------------------------------------------------
    def test_mutant_no_rebuild_makes_one_rebuild_differ(self):
        work = self._work()
        with mock.patch.object(fc.HelperWalk, "REBUILDS", 0):
            self.assertEqual(fc.HelperWalk.REBUILDS, 0)
            mutant = fc.HelperWalk().run("one-rebuild", self.vc_root, work)
        got = fc.normalise_outputs(mutant, work, self.vc_root)
        self.assertNotEqual(
            _outcome_differences(_recorded(self.record, "one-rebuild"), got),
            [])

    def test_edit_during_card_reopens_the_verdict(self):
        after, walk = edit_during_card(fc.HelperWalk(), self.vc_root,
                                       self._work())
        self.assertEqual((after or {}).get("action"), "outstanding-to-phase-5")
        self.assertEqual(walk.results[-1]["counts"]["outstanding_cw_hashes"],
                         [ARCH_HASH])
        self.assertIsNone(walk.stop_sentence)

    def test_mutant_reused_blobfile_makes_the_edit_check_differ(self):
        real_fence = fc._HelperSteps.fence
        mint = 'BLOBFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX")'

        def reuse_first_blobfile(walk, needle):
            body = real_fence(walk, needle)
            if needle != fc.FINALIZE_INPUTS_CALL or not walk.blobfiles:
                return body
            mutated = body.replace(mint, 'BLOBFILE="%s"' % walk.blobfiles[0])
            self.assertNotEqual(mutated, body)
            return mutated
        with mock.patch.object(fc._HelperSteps, "fence",
                               reuse_first_blobfile):
            self.assertIs(fc._HelperSteps.fence, reuse_first_blobfile)
            after, walk = edit_during_card(fc.HelperWalk(), self.vc_root,
                                           self._work())
        blobs = walk.blobfiles
        self.assertEqual(len(set(blobs)), 1, blobs)
        self.assertNotEqual((after or {}).get("action"),
                            "outstanding-to-phase-5")

    def test_report_failure_stops_at_once(self):
        tree = fc.report_stand_in_root(self.vc_root, self._work())
        out = fc.HelperWalk().run("clean-close", tree, self._work())
        self.assertEqual(out["stop_sentence"], REPORT_HALT)
        self.assertEqual([s["exit"] for s in _inputs_steps(out)], [5])
        self.assertEqual((out["files_written"], out["files_archived"],
                          out["state_closed"], out["gate"]),
                         ([fc.STATE_REL], [], False, []))

    def test_mutant_ignoring_exit_five_makes_the_report_leg_differ(self):
        tree = fc.report_stand_in_root(self.vc_root, self._work())
        with mock.patch.object(fc.HelperWalk, "STOP_AT_ONCE", ()):
            self.assertEqual(fc.HelperWalk.STOP_AT_ONCE, ())
            out = fc.HelperWalk().run("clean-close", tree, self._work())
        self.assertNotEqual(out["stop_sentence"], REPORT_HALT)
        self.assertEqual(len(_inputs_steps(out)), 2)


# --------------------------------------------------------------------------- #
# compare, the like-for-like 2.14.1 run and the screen text (D-15, D-18)
# --------------------------------------------------------------------------- #
README = os.path.join(REPO, "docs", "design", "lean-v2.15", "README.md")


def _main(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = fc.main(argv)
    return rc, out.getvalue(), err.getvalue()


class TestCompare(_CandidateTree):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.fresh = fc.capture_candidate(REPO, root=LIVE_PLUGIN)
        except BaseException:
            shutil.rmtree(cls._tmp, True)
            raise

    def _record_copy(self, mutate):
        record = _record()
        mutate(record)
        path = os.path.join(self._work(), "record.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fc.record_text(record))
        return path

    def test_outcome_fields_match_and_only_steps_and_tally_differ(self):
        problems, intended = fc.compare(REPO, RECORD, root=LIVE_PLUGIN,
                                        fresh=self.fresh)
        self.assertEqual(problems, [])
        self.assertTrue(intended)
        for line in intended:
            field = line.split(": ", 2)[1]
            self.assertTrue(field.startswith(("steps", "tally.")), line)
        self.assertIn("clean-close: tally.commands_run: before 8, after 3",
                      intended)

    def test_altered_stop_sentence_is_named_and_fails(self):
        def mutate(record):
            sit = record["situations"]["refused-close"]
            old = sit["stop_sentence"]
            sit["stop_sentence"] = old.replace("again", "once more")
            self.assertNotEqual(sit["stop_sentence"], old)
        path = self._record_copy(mutate)
        problems, _ = fc.compare(REPO, path, root=LIVE_PLUGIN,
                                 fresh=self.fresh)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("refused-close: stop_sentence"))
        self.assertIn("once more", problems[0])
        self.assertIn("run `--finalize` again", problems[0])

    def test_altered_tally_does_not_fail(self):
        def mutate(record):
            record["situations"]["clean-close"]["tally"]["commands_run"] += 7
        path = self._record_copy(mutate)
        problems, intended = fc.compare(REPO, path, root=LIVE_PLUGIN,
                                        fresh=self.fresh)
        self.assertEqual(problems, [])
        self.assertIn("clean-close: tally.commands_run: before 15, after 3",
                      intended)

    def test_cli_exit_codes(self):
        base = ["compare", "--repo", REPO, "--record", RECORD,
                "--driver", "helper"]
        with self.subTest("neither --commit nor --root"):
            self.assertEqual(_main(base)[0], 2)
        with self.subTest("both --commit and --root"):
            self.assertEqual(_main(base + ["--commit", "HEAD", "--root",
                                           LIVE_PLUGIN])[0], 2)
        with self.subTest("an unknown driver"):
            self.assertEqual(_main(["compare", "--repo", REPO, "--record",
                                    RECORD, "--driver", "fence", "--root",
                                    LIVE_PLUGIN])[0], 2)
        with self.subTest("an altered stop sentence"):
            def mutate(record):
                record["situations"]["refused-close"]["stop_sentence"] = "x"
            rc, out, _ = _main(["compare", "--repo", REPO, "--record",
                                self._record_copy(mutate), "--driver",
                                "helper", "--root", LIVE_PLUGIN])
            self.assertEqual(rc, 1)
            self.assertIn("refused-close: stop_sentence", out)

    def test_cli_root_and_commit_match(self):
        head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=30,
                              check=True).stdout.strip()
        for where in (["--root", LIVE_PLUGIN], ["--commit", head]):
            with self.subTest(where[0]):
                rc, out, err = _main(["compare", "--repo", REPO, "--record",
                                      RECORD, "--driver", "helper"] + where)
                self.assertEqual(rc, 0, out + err)
                for sid in SITUATION_IDS:
                    self.assertIn("%s: outcome fields match" % sid, out)
                self.assertIn("one-rebuild/second-failure: outcome fields "
                              "match", out)
                self.assertIn("finalize outcome fields match", out)

    def test_compare_drives_the_new_instructions(self):
        """Not decorative: a break in the copied 90-finalize.md, and one in
        the copied helper, each make compare fail."""
        stop = fc.stop_sentence(self.finalize_text)
        breaks = (
            ("90-finalize.md: the stop sentence",
             ("phases", "shared", "90-finalize.md"), stop,
             stop.replace("again", "once more")),
            ("finalize_inputs.py: the gate reason",
             ("scripts", "finalize_inputs.py"),
             '{"action": action, "reason": reason,',
             '{"action": action, "reason": reason + "!",'))
        for name, rel, old, new in breaks:
            with self.subTest(name):
                tree = os.path.join(self._work(), "vc")
                shutil.copytree(LIVE_PLUGIN, tree, ignore=shutil.ignore_patterns(
                    "__pycache__"))
                path = os.path.join(tree, *rel)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                self.assertIn(old, text)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text.replace(old, new))
                problems, _ = fc.compare(REPO, RECORD, root=tree)
                self.assertTrue(problems, name)


class TestLikeForLike(_PinnedTree):
    """The 2.14.1 tree given the candidate's stand-in for the malformed
    input: `not json` in the printed BLOBFILE on both attempts."""

    def test_refused_close_outcome_equals_the_record(self):
        work = tempfile.mkdtemp(prefix="fc-lfl-", dir=self._tmp)
        driver = fc.LikeForLike2141()
        out = driver.run("refused-close", self.vc_root, work)
        got = fc.normalise_outputs(out, work, self.vc_root)
        self.assertEqual(_outcome_differences(
            _recorded(_record(), "refused-close"), got), [])
        self.assertEqual([s["exit"] for s in _steps(out, "counts")], [1, 1])
        self.assertEqual(_steps(out, "gate"), [])
        self.assertEqual(fc.like_for_like(REPO, _record()), [])

    def test_the_stand_in_really_reached_the_counts_step(self):
        work = tempfile.mkdtemp(prefix="fc-lfl-", dir=self._tmp)
        driver = fc.LikeForLike2141()
        driver.run("refused-close", self.vc_root, work)
        for rc, err in driver.last_walk.attempt_stderr:
            self.assertEqual(rc, 1)
            self.assertEqual(err.splitlines()[-1], COUNTS_HALT)


class TestScreenText(_CandidateTree):
    """D-18: the same lines in the same place on both versions."""

    def test_counting_lines_are_byte_identical(self):
        screens = fc.counting_screens(REPO, LIVE_PLUGIN)
        self.assertEqual(sorted(screens), ["missing", "not json"])
        for fault, (old, new) in screens.items():
            with self.subTest(fault):
                self.assertEqual(old, new)
                self.assertEqual(len(new.splitlines()), 2, new)
                self.assertEqual(new.splitlines()[1], COUNTS_HALT)
                altered = new[:3] + ("X" if new[3] != "X" else "Y") + new[4:]
                self.assertNotEqual(altered, new)
                self.assertFalse(fc.screen_matches(old, altered))
                self.assertTrue(fc.screen_matches(old, new))

    def test_report_lines_are_byte_identical(self):
        old, new = fc.report_screens(REPO, LIVE_PLUGIN)
        self.assertEqual(old, new)
        self.assertEqual(len(new.splitlines()), 2, new)
        self.assertEqual(new.splitlines()[1], REPORT_HALT)
        self.assertNotIn("Traceback", new)

    def test_readme_names_compare(self):
        with open(README, encoding="utf-8") as fh:
            row = [line for line in fh if line.startswith(
                "| `finalize_capture.py`")]
        self.assertEqual(len(row), 1)
        self.assertIn("compare", row[0])
        self.assertIn("--driver helper", row[0])


if __name__ == "__main__":
    unittest.main()
