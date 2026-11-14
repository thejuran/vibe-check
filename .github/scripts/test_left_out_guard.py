"""Tests for left_out_guard.py, the CI guard for left-out and skipped tests.

Three locks, each with one mutant per rule:
- check-list / args: the left-out list must be exactly the five recorded ids.
- check-log: the suite's summary line must show exactly 5 deselected and no
  failure or error, so a left-out id that matches no real test is caught.
- check-skips: the tests that skipped themselves (read from pytest's junit
  result file) must equal the recorded (test id, reason) set, and an
  unrecorded list never passes.

Every mutant starts from a passing input, asserts it passes, applies one
change, asserts the input really changed, then asserts the failure.
"""

import ast
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from xml.sax.saxutils import quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import left_out_guard as log_guard  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD_PY = os.path.join(HERE, "left_out_guard.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LIST_FILE = os.path.join(REPO_ROOT, ".github", "ci-left-out-tests.txt")

LIST_STOP = "LEFT-OUT LIST DIFFERS FROM THE RECORDED FIVE — STOPPING"
DESELECT_STOP = "DESELECT COUNT IS NOT 5 — STOPPING"
FAILURE_STOP = "SUITE LOG SHOWS A FAILURE — STOPPING"
NOT_RECORDED_STOP = "SKIP LIST NOT YET RECORDED — THIS IS A RECORDING RUN, NOT A GREEN RUN — STOPPING"
SKIP_STOP = "SKIPPED SET DIFFERS FROM THE RECORDED LIST — STOPPING"
COUNT_STOP = "SKIP COUNT IN THE LOG AND THE RESULT FILE DISAGREE — STOPPING"

GOOD_SUMMARY = "3883 passed, 2 skipped, 5 deselected, 5060 subtests passed in 201.00s"

REPLAY = "plugins/vibe-check/scripts/test_replay.py::"
LANE = "plugins/vibe-check/scripts/test_lanearchive.py::"
REPLAY_REASON = ("Phase-40 transcripts are local-only (gitignored); "
                 "a linked worktree has none to recover from")
LANE_REASON = "no sandbox temp root on this machine"

REPLAY_SKIP_ID = REPLAY + "TestReconstruction::test_transcript_recovery_covers_survivor_agents"
LANE_SKIP_ID = LANE + "TestLocateCodexDir::test_real_sandbox_root_tmp_and_private_tmp_forms"
GOOD_PAIRS = ((LANE_SKIP_ID, LANE_REASON), (REPLAY_SKIP_ID, REPLAY_REASON))

# (classname, name, skip reason or None) rows for the synthetic result file.
GOOD_CASES = [
    ("plugins.vibe-check.scripts.test_replay.TestReconstruction",
     "test_transcript_recovery_covers_survivor_agents", REPLAY_REASON),
    ("plugins.vibe-check.scripts.test_lanearchive.TestLocateCodexDir",
     "test_real_sandbox_root_tmp_and_private_tmp_forms", LANE_REASON),
    ("plugins.vibe-check.scripts.test_replay.TestCensus", "test_census", None),
    ("plugins.vibe-check.scripts.test_footprint.TestImportSet", "test_imports", None),
]


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = log_guard.main(argv)
    return code, out.getvalue(), err.getvalue()


def junit_text(cases):
    rows = []
    for classname, name, reason in cases:
        if reason is None:
            rows.append('<testcase classname=%s name=%s time="0.001" />'
                        % (quoteattr(classname), quoteattr(name)))
        else:
            rows.append('<testcase classname=%s name=%s time="0.000">'
                        '<skipped type="pytest.skip" message=%s>file.py:1: %s</skipped>'
                        '</testcase>' % (quoteattr(classname), quoteattr(name),
                                         quoteattr(reason), reason))
    skipped = sum(1 for c in cases if c[2] is not None)
    return ('<?xml version="1.0" encoding="utf-8"?><testsuites name="pytest tests">'
            '<testsuite name="pytest" errors="0" failures="0" skipped="%d" tests="%d">%s'
            '</testsuite></testsuites>' % (skipped, len(cases), "".join(rows)))


def log_text(summary):
    return ("....................................................... [ 99%%]\n"
            "SKIPPED [1] plugins/vibe-check/scripts/test_replay.py:281: whatever\n"
            "%s\n" % summary)


class TmpCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name, text):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path


# --------------------------------------------------------------------------
# check-list and args (D-18)
# --------------------------------------------------------------------------

class TestCheckList(TmpCase):
    def good_text(self):
        return "\n".join(log_guard.RECORDED_FIVE) + "\n"

    def assert_list_trips(self, mutant, named):
        good = self.good_text()
        self.assertEqual(run_main(["check-list", self.write("good.txt", good)])[0], 0)
        self.assertNotEqual(mutant, good)
        code, out, err = run_main(["check-list", self.write("bad.txt", mutant)])
        self.assertEqual(code, 1)
        self.assertIn(LIST_STOP, err)
        self.assertIn(named, err)
        self.assertNotIn("left-out list matches", out)

    def test_exact_five_any_order_with_blank_lines_passes(self):
        text = "\n\n".join(reversed(log_guard.RECORDED_FIVE)) + "\n\n"
        code, out, _err = run_main(["check-list", self.write("l.txt", text)])
        self.assertEqual(code, 0)
        self.assertIn("left-out list matches the recorded five", out)

    def test_committed_list_file_passes(self):
        code, out, _err = run_main(["check-list", LIST_FILE])
        self.assertEqual(code, 0)
        self.assertIn("left-out list matches the recorded five", out)

    def test_committed_list_file_shape(self):
        with open(LIST_FILE, encoding="utf-8") as fh:
            lines = [l for l in fh.read().splitlines() if l.strip()]
        self.assertEqual(len(lines), 5)
        self.assertEqual(sum("test_replay.py::TestPhase53SameLineRegressionCases::" in l
                             for l in lines), 3)
        self.assertEqual(sum("test_footprint.py::TestWordCountLocaleDrift::" in l
                             for l in lines), 2)

    def test_mutant_sixth_id_added(self):
        extra = REPLAY + "TestCensus::test_census"
        self.assert_list_trips(self.good_text() + extra + "\n", extra)

    def test_mutant_one_id_removed(self):
        gone = log_guard.RECORDED_FIVE[2]
        mutant = "\n".join(log_guard.RECORDED_FIVE[:2] + log_guard.RECORDED_FIVE[3:]) + "\n"
        self.assert_list_trips(mutant, gone)

    def test_mutant_one_id_altered_by_a_character(self):
        orig = log_guard.RECORDED_FIVE[0]
        altered = orig[:-1] + ("x" if orig[-1] != "x" else "y")
        self.assertIn(orig, self.good_text())
        self.assert_list_trips(self.good_text().replace(orig, altered, 1), altered)

    def test_mutant_one_id_duplicated(self):
        dup = log_guard.RECORDED_FIVE[4]
        self.assert_list_trips(self.good_text() + dup + "\n", dup)

    def test_mutant_comment_line_added(self):
        self.assert_list_trips("# the five Linux-impossible tests\n" + self.good_text(),
                               "# the five Linux-impossible tests")

    def test_mutant_free_text_line_added(self):
        self.assert_list_trips(self.good_text() + "see 62-RESEARCH.md\n",
                               "see 62-RESEARCH.md")

    def test_missing_file_exits_2(self):
        code, _out, err = run_main(["check-list", os.path.join(self.tmp, "nope.txt")])
        self.assertEqual(code, 2)
        self.assertIn("— STOPPING", err)


class TestArgs(TmpCase):
    def test_good_file_prints_five_deselects_in_recorded_order(self):
        text = "\n".join(reversed(log_guard.RECORDED_FIVE)) + "\n"
        code, out, _err = run_main(["args", self.write("l.txt", text)])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(),
                         ["--deselect=" + i for i in log_guard.RECORDED_FIVE])

    def test_bad_file_prints_no_deselect(self):
        good = "\n".join(log_guard.RECORDED_FIVE) + "\n"
        self.assertEqual(run_main(["args", self.write("g.txt", good)])[0], 0)
        mutant = good + "plugins/vibe-check/scripts/test_score.py::TestX::test_y\n"
        self.assertNotEqual(mutant, good)
        code, out, err = run_main(["args", self.write("b.txt", mutant)])
        self.assertEqual(code, 1)
        self.assertNotIn("--deselect", out)
        self.assertIn(LIST_STOP, err)

    def test_args_emits_constant_not_file_text(self):
        # The emitted ids come from the in-code constant; every one is free of
        # shell metacharacters (T-62-03).
        for i in log_guard.RECORDED_FIVE:
            self.assertRegex(i, r"^[A-Za-z0-9_./:-]+$")


# --------------------------------------------------------------------------
# check-log (D-18: the five must really match five tests)
# --------------------------------------------------------------------------

class TestCheckLog(TmpCase):
    def assert_log_trips(self, mutant_summary, message, whole=None):
        good = log_text(GOOD_SUMMARY)
        self.assertEqual(run_main(["check-log", self.write("good.log", good)])[0], 0)
        mutant = whole if whole is not None else log_text(mutant_summary)
        self.assertNotEqual(mutant, good)
        code, _out, err = run_main(["check-log", self.write("bad.log", mutant)])
        self.assertEqual(code, 1)
        self.assertIn(message, err)

    def test_good_log_passes_and_holds_skips(self):
        self.assertIn("2 skipped", GOOD_SUMMARY)
        code, out, _err = run_main(["check-log", self.write("g.log", log_text(GOOD_SUMMARY))])
        self.assertEqual(code, 0)
        self.assertIn("5 deselected", out)

    def test_bordered_summary_line_passes(self):
        text = log_text("=== %s ===" % GOOD_SUMMARY)
        self.assertEqual(run_main(["check-log", self.write("g.log", text)])[0], 0)

    def test_mutant_4_deselected(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" 5 deselected", " 4 deselected"),
                              DESELECT_STOP)

    def test_mutant_6_deselected(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" 5 deselected", " 6 deselected"),
                              DESELECT_STOP)

    def test_mutant_15_deselected(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" 5 deselected", " 15 deselected"),
                              DESELECT_STOP)

    def test_mutant_no_deselected_token(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" 5 deselected,", ""), DESELECT_STOP)

    def test_mutant_one_failed(self):
        self.assert_log_trips("1 failed, " + GOOD_SUMMARY, FAILURE_STOP)

    def test_mutant_one_error(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" in 201", ", 1 error in 201"),
                              FAILURE_STOP)

    def test_mutant_errors_plural(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" in 201", ", 27 errors in 201"),
                              FAILURE_STOP)

    def test_mutant_subtests_failed(self):
        self.assert_log_trips(GOOD_SUMMARY.replace(" in 201", ", 3 subtests failed in 201"),
                              FAILURE_STOP)

    def test_mutant_empty_log(self):
        self.assert_log_trips(None, DESELECT_STOP, whole="")

    def test_mutant_no_summary_line(self):
        self.assert_log_trips(None, DESELECT_STOP,
                              whole="collected 3888 items / 5 deselected\n....\n")

    def test_last_summary_line_wins(self):
        text = log_text(GOOD_SUMMARY) + "1 failed, 2 passed, 5 deselected in 0.1s\n"
        code, _out, err = run_main(["check-log", self.write("l.log", text)])
        self.assertEqual(code, 1)
        self.assertIn(FAILURE_STOP, err)

    def test_missing_log_exits_2(self):
        code, _out, _err = run_main(["check-log", os.path.join(self.tmp, "nope.log")])
        self.assertEqual(code, 2)


# --------------------------------------------------------------------------
# check-skips (D-20)
# --------------------------------------------------------------------------

class SkipCase(TmpCase):
    def files(self, cases=None, summary=GOOD_SUMMARY):
        cases = GOOD_CASES if cases is None else cases
        return (self.write("r.xml", junit_text(cases)), self.write("s.log", log_text(summary)))

    def skips(self, recorded, cases=None, summary=GOOD_SUMMARY):
        xml, logp = self.files(cases, summary)
        with mock.patch.object(log_guard, "RECORDED_SKIPS", recorded):
            return run_main(["check-skips", xml, logp])

    def assert_good_passes(self):
        code, out, _err = self.skips(GOOD_PAIRS)
        self.assertEqual(code, 0)
        self.assertIn("skipped set matches the recorded 2", out)


class TestCheckSkipsNotRecorded(SkipCase):
    def test_none_is_a_recording_run_and_prints_observed(self):
        code, out, err = self.skips(None)
        self.assertEqual(code, 1)
        self.assertIn(NOT_RECORDED_STOP, err)
        lines = [l for l in out.splitlines() if l.startswith("OBSERVED-SKIP\t")]
        self.assertEqual(lines, ["OBSERVED-SKIP\t%s\t%s" % p for p in sorted(GOOD_PAIRS)])
        self.assertIn("OBSERVED-SKIP-COUNT 2", out)

    def test_none_with_no_skips_still_exits_1(self):
        cases = [c for c in GOOD_CASES if c[2] is None]
        code, out, err = self.skips(None, cases, GOOD_SUMMARY.replace(" 2 skipped,", ""))
        self.assertEqual(code, 1)
        self.assertIn(NOT_RECORDED_STOP, err)
        self.assertIn("OBSERVED-SKIP-COUNT 0", out)


# The list pinned from the runner's recording run (D-20).
RECORDED_SKIP_COUNT_AT_PIN = 2
EXTRA_SKIP_PAIR = (REPLAY + "TestCensus::test_census", REPLAY_REASON)


def _cases_skipping(pairs):
    """Synthetic result-file rows that skip exactly `pairs`, plus two that ran."""
    rows = []
    for test_id, reason in pairs:
        path, cls, func = test_id.split("::")
        module = path[:-len(".py")].replace("/", ".")
        rows.append(("%s.%s" % (module, cls), func, reason))
    rows.append(("plugins.vibe-check.scripts.test_replay.TestCensus", "test_census", None))
    rows.append(("plugins.vibe-check.scripts.test_footprint.TestImportSet", "test_imports", None))
    return rows


class TestPinnedSkipList(SkipCase):
    def pinned_files(self):
        pinned = log_guard.RECORDED_SKIPS
        summary = ("4319 passed, %d skipped, 5 deselected, 5298 subtests passed in 209.65s"
                   % len(pinned))
        return self.files(_cases_skipping(pinned), summary)

    def run_pinned(self, recorded):
        xml, logp = self.pinned_files()
        with mock.patch.object(log_guard, "RECORDED_SKIPS", recorded):
            return run_main(["check-skips", xml, logp])

    def test_skip_list_is_recorded(self):
        pinned = log_guard.RECORDED_SKIPS
        self.assertIsNotNone(pinned)
        self.assertEqual(len(pinned), RECORDED_SKIP_COUNT_AT_PIN)
        self.assertEqual(log_guard.skip_list_problems(pinned), [])
        for test_id, _reason in pinned:
            with self.subTest(test_id=test_id):
                path, cls, func = test_id.split("::")
                classes = [n for n in _parse(path).body
                           if isinstance(n, ast.ClassDef) and n.name == cls]
                self.assertEqual(len(classes), 1, cls)
                funcs = {n.name for n in classes[0].body if isinstance(n, ast.FunctionDef)}
                self.assertIn(func, funcs)

    def test_pinned_set_passes_unpatched(self):
        xml, logp = self.pinned_files()
        code, out, _err = run_main(["check-skips", xml, logp])
        self.assertEqual(code, 0)
        self.assertIn("skipped set matches the recorded %d" % RECORDED_SKIP_COUNT_AT_PIN, out)

    def test_break_back_to_none_is_a_recording_run(self):
        code, _out, err = self.run_pinned(None)
        self.assertEqual(code, 1)
        self.assertIn(NOT_RECORDED_STOP, err)

    def test_break_one_pair_removed_reports_unexpected(self):
        pinned = log_guard.RECORDED_SKIPS
        removed = pinned[1:]
        self.assertEqual(len(removed), len(pinned) - 1)
        code, _out, err = self.run_pinned(removed)
        self.assertEqual(code, 1)
        self.assertIn(SKIP_STOP, err)
        self.assertIn("unexpected %s — %s" % pinned[0], err)

    def test_break_one_pair_added_reports_missing(self):
        pinned = log_guard.RECORDED_SKIPS
        self.assertNotIn(EXTRA_SKIP_PAIR, pinned)
        added = tuple(sorted(pinned + (EXTRA_SKIP_PAIR,)))
        self.assertEqual(len(added), len(pinned) + 1)
        code, _out, err = self.run_pinned(added)
        self.assertEqual(code, 1)
        self.assertIn(SKIP_STOP, err)
        self.assertIn("missing %s — %s" % EXTRA_SKIP_PAIR, err)

    def test_break_one_reason_changed_reports_unexpected_and_missing(self):
        pinned = log_guard.RECORDED_SKIPS
        test_id, reason = pinned[0]
        changed_reason = reason[:-1] + ("X" if reason[-1] != "X" else "Y")
        changed = ((test_id, changed_reason),) + pinned[1:]
        self.assertNotEqual(changed, pinned)
        # The runtime rule refuses a reason that is not the approved one for its file.
        code, _out, err = self.run_pinned(changed)
        self.assertEqual(code, 1)
        self.assertIn("RECORDED SKIP LIST BREAKS THE APPROVED-GROUP RULE — STOPPING", err)
        # With the rule moved to the changed reason too, the set comparison still
        # catches it on its own: both directions name the id.
        prefix = test_id.split("::")[0] + "::"
        approved = tuple((p, changed_reason if p == prefix else r)
                         for p, r in log_guard.APPROVED_SKIP_REASONS)
        self.assertNotEqual(approved, log_guard.APPROVED_SKIP_REASONS)
        with mock.patch.object(log_guard, "APPROVED_SKIP_REASONS", approved):
            code, _out, err = self.run_pinned(changed)
        self.assertEqual(code, 1)
        self.assertIn(SKIP_STOP, err)
        self.assertIn("unexpected %s — %s" % (test_id, reason), err)
        self.assertIn("missing %s — %s" % (test_id, changed_reason), err)


class TestCheckSkipsMatch(SkipCase):
    def test_recorded_pairs_match(self):
        self.assert_good_passes()

    def test_empty_recorded_against_no_skips(self):
        cases = [c for c in GOOD_CASES if c[2] is None]
        code, out, _err = self.skips((), cases, GOOD_SUMMARY.replace(" 2 skipped,", ""))
        self.assertEqual(code, 0)
        self.assertIn("skipped set matches the recorded 0", out)

    def test_observed_skips_builds_ids(self):
        xml, _ = self.files()
        self.assertEqual(log_guard.observed_skips(xml), sorted(GOOD_PAIRS))


class TestCheckSkipsMutants(SkipCase):
    def assert_skip_trips(self, recorded, cases, needle, summary=None):
        self.assert_good_passes()
        if summary is None:
            n = sum(1 for c in cases if c[2] is not None)
            summary = GOOD_SUMMARY.replace("2 skipped", "%d skipped" % n)
        self.assertTrue(recorded != GOOD_PAIRS or cases != GOOD_CASES)
        if cases != GOOD_CASES:
            self.assertNotEqual(junit_text(cases), junit_text(GOOD_CASES))
        code, _out, err = self.skips(recorded, cases, summary)
        self.assertEqual(code, 1)
        self.assertIn(SKIP_STOP, err)
        self.assertIn(needle, err)

    def test_mutant_one_more_skipped_test(self):
        extra = ("plugins.vibe-check.scripts.test_replay.TestCensus", "test_more", REPLAY_REASON)
        self.assert_skip_trips(GOOD_PAIRS, GOOD_CASES + [extra],
                               "unexpected " + REPLAY + "TestCensus::test_more")

    def test_mutant_recorded_test_ran_instead(self):
        cases = [c if c[1] != "test_real_sandbox_root_tmp_and_private_tmp_forms"
                 else (c[0], c[1], None) for c in GOOD_CASES]
        self.assert_skip_trips(GOOD_PAIRS, cases, "missing " + LANE_SKIP_ID)

    def test_mutant_different_id_same_reason(self):
        cases = [c if c[1] != "test_transcript_recovery_covers_survivor_agents"
                 else (c[0], "test_other_recovery", c[2]) for c in GOOD_CASES]
        self.assert_skip_trips(GOOD_PAIRS, cases,
                               "unexpected " + REPLAY + "TestReconstruction::test_other_recovery")

    def test_mutant_same_id_reason_changed_by_one_character(self):
        changed = LANE_REASON[:-1] + "E"
        self.assertNotEqual(changed, LANE_REASON)
        cases = [c if c[2] != LANE_REASON else (c[0], c[1], changed) for c in GOOD_CASES]
        self.assert_skip_trips(GOOD_PAIRS, cases, "unexpected " + LANE_SKIP_ID)

    def test_mutant_recorded_empty_against_one_skip(self):
        cases = [c for c in GOOD_CASES if c[2] != LANE_REASON]
        self.assert_skip_trips((), cases, "unexpected " + REPLAY_SKIP_ID)

    def test_mutant_recorded_pair_against_no_skips(self):
        cases = [c for c in GOOD_CASES if c[2] is None]
        self.assert_skip_trips(((REPLAY_SKIP_ID, REPLAY_REASON),), cases,
                               "missing " + REPLAY_SKIP_ID,
                               summary=GOOD_SUMMARY.replace(" 2 skipped,", ""))

    def test_mutant_classname_outside_plugin_scripts(self):
        extra = ("docs.design.lean-v2.15.tools.test_x.TestY", "test_z", "why")
        self.assert_skip_trips(GOOD_PAIRS, GOOD_CASES + [extra],
                               "unexpected docs.design.lean-v2.15.tools.test_x.TestY::test_z")


class TestCheckSkipsCount(SkipCase):
    def test_log_says_3_result_file_has_2(self):
        self.assert_good_passes()
        code, _out, err = self.skips(GOOD_PAIRS, GOOD_CASES,
                                     GOOD_SUMMARY.replace("2 skipped", "3 skipped"))
        self.assertEqual(code, 1)
        self.assertIn(COUNT_STOP, err)

    def test_no_skipped_token_counts_as_zero(self):
        self.assert_good_passes()
        summary = GOOD_SUMMARY.replace(" 2 skipped,", "")
        self.assertNotIn("skipped", summary)
        code, _out, err = self.skips(GOOD_PAIRS, GOOD_CASES, summary)
        self.assertEqual(code, 1)
        self.assertIn(COUNT_STOP, err)

    def test_subtests_skipped_is_not_the_test_count(self):
        # No test-level skips, only subtest skips: the count must read 0.
        cases = [c for c in GOOD_CASES if c[2] is None]
        summary = GOOD_SUMMARY.replace(" 2 skipped,", "").replace(
            " in 201", ", 4 subtests skipped in 201")
        self.assertNotIn(" 2 skipped", summary)
        self.assertIn("4 subtests skipped", summary)
        code, out, err = self.skips((), cases, summary)
        self.assertEqual(code, 0, err)
        self.assertIn("skipped set matches the recorded 0", out)


class TestCheckSkipsUnusable(SkipCase):
    def run_with(self, xml_path, logp=None):
        logp = logp or self.write("s.log", log_text(GOOD_SUMMARY))
        with mock.patch.object(log_guard, "RECORDED_SKIPS", GOOD_PAIRS):
            return run_main(["check-skips", xml_path, logp])

    def test_missing_result_file(self):
        self.assertEqual(self.run_with(os.path.join(self.tmp, "nope.xml"))[0], 2)

    def test_unparseable_result_file(self):
        self.assertEqual(self.run_with(self.write("b.xml", "<testsuites><testcase"))[0], 2)

    def test_zero_testcases(self):
        self.assertEqual(self.run_with(self.write("e.xml", junit_text([])))[0], 2)

    def test_oversized_result_file(self):
        path = self.write("big.xml", junit_text(GOOD_CASES))
        with mock.patch.object(log_guard, "MAX_RESULT_BYTES", 10):
            code, _out, err = self.run_with(path)
        self.assertEqual(code, 2)
        # Refused for its size, before any parse is attempted.
        self.assertIn("RESULT FILE OVER 10 BYTES", err)
        self.assertNotIn("CANNOT PARSE", err)

    def test_size_cap_is_50_mb(self):
        self.assertEqual(log_guard.MAX_RESULT_BYTES, 50 * 1024 * 1024)

    def test_missing_log(self):
        xml = self.write("r.xml", junit_text(GOOD_CASES))
        self.assertEqual(self.run_with(xml, os.path.join(self.tmp, "nope.log"))[0], 2)

    def test_cli_nonexistent_exits_2(self):
        proc = subprocess.run([sys.executable, "-I", GUARD_PY, "check-skips",
                               "/nonexistent.xml", "/nonexistent.log"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 2)


class TestRecordedListRuleAtRuntime(SkipCase):
    def test_bad_recorded_list_is_refused_even_if_sets_match(self):
        self.assert_good_passes()
        bad_id = "plugins/vibe-check/scripts/test_score.py::TestX::test_y"
        cases = GOOD_CASES + [("plugins.vibe-check.scripts.test_score.TestX", "test_y", "r")]
        recorded = GOOD_PAIRS + ((bad_id, "r"),)
        code, _out, err = self.skips(recorded, cases,
                                     GOOD_SUMMARY.replace("2 skipped", "3 skipped"))
        self.assertEqual(code, 1)
        self.assertIn(bad_id, err)


# --------------------------------------------------------------------------
# Class rule on the recorded list (D-20)
# --------------------------------------------------------------------------

class TestSkipListProblems(unittest.TestCase):
    def assert_rule_trips(self, mutant, needle):
        self.assertEqual(log_guard.skip_list_problems(GOOD_PAIRS), [])
        self.assertNotEqual(mutant, GOOD_PAIRS)
        problems = log_guard.skip_list_problems(mutant)
        self.assertNotEqual(problems, [])
        self.assertTrue(any(needle in p for p in problems), problems)

    def test_none_and_empty_and_good_pass(self):
        self.assertEqual(log_guard.skip_list_problems(None), [])
        self.assertEqual(log_guard.skip_list_problems(()), [])
        self.assertEqual(log_guard.skip_list_problems(GOOD_PAIRS), [])

    def test_mutant_id_under_test_score(self):
        bad = "plugins/vibe-check/scripts/test_score.py::TestX::test_y"
        self.assert_rule_trips(GOOD_PAIRS + ((bad, LANE_REASON),), bad)

    def test_mutant_id_is_one_of_the_five(self):
        five = log_guard.RECORDED_FIVE[0]
        self.assert_rule_trips(GOOD_PAIRS + ((five, REPLAY_REASON),), five)

    def test_mutant_empty_reason(self):
        mutant = ((LANE_SKIP_ID, ""), GOOD_PAIRS[1])
        self.assert_rule_trips(mutant, "empty reason: " + LANE_SKIP_ID)

    def test_mutant_duplicated_id(self):
        self.assert_rule_trips(GOOD_PAIRS + (GOOD_PAIRS[1],), REPLAY_SKIP_ID)

    def test_mutant_replay_id_with_lanearchive_reason(self):
        mutant = (GOOD_PAIRS[0], (REPLAY_SKIP_ID, LANE_REASON))
        self.assert_rule_trips(mutant, REPLAY_SKIP_ID)

    def test_mutant_lanearchive_reason_off_by_one_character(self):
        changed = LANE_REASON.replace("sandbox", "sandbax")
        self.assertNotEqual(changed, LANE_REASON)
        mutant = ((LANE_SKIP_ID, changed), GOOD_PAIRS[1])
        self.assert_rule_trips(mutant, LANE_SKIP_ID)

    def test_approved_reasons_constant(self):
        self.assertEqual(log_guard.APPROVED_SKIP_REASONS,
                         ((REPLAY, REPLAY_REASON), (LANE, LANE_REASON)))


# --------------------------------------------------------------------------
# Fixture checks against the real plugin test files (read, never edited)
# --------------------------------------------------------------------------

def _parse(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path), encoding="utf-8") as fh:
        return ast.parse(fh.read())


def _string_constants(rel_path):
    return {n.value for n in ast.walk(_parse(rel_path))
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


class TestRecordedIdsExist(unittest.TestCase):
    def test_each_recorded_id_names_a_real_class_and_function(self):
        self.assertEqual(len(log_guard.RECORDED_FIVE), 5)
        self.assertEqual(len(set(log_guard.RECORDED_FIVE)), 5)
        for test_id in log_guard.RECORDED_FIVE:
            with self.subTest(test_id=test_id):
                path, cls, func = test_id.split("::")
                self.assertTrue(os.path.isfile(os.path.join(REPO_ROOT, path)), path)
                classes = [n for n in _parse(path).body
                           if isinstance(n, ast.ClassDef) and n.name == cls]
                self.assertEqual(len(classes), 1, cls)
                funcs = {n.name for n in classes[0].body if isinstance(n, ast.FunctionDef)}
                self.assertIn(func, funcs)

    def test_lookup_break_finds_nothing_for_an_altered_name(self):
        path, cls, func = log_guard.RECORDED_FIVE[0].split("::")
        classes = [n for n in _parse(path).body
                   if isinstance(n, ast.ClassDef) and n.name == cls]
        funcs = {n.name for n in classes[0].body if isinstance(n, ast.FunctionDef)}
        self.assertNotIn(func + "x", funcs)


class TestApprovedReasonsExistInFiles(unittest.TestCase):
    def test_each_reason_is_a_string_constant_in_its_file(self):
        self.assertEqual(len(log_guard.APPROVED_SKIP_REASONS), 2)
        for prefix, reason in log_guard.APPROVED_SKIP_REASONS:
            with self.subTest(prefix=prefix):
                path = prefix.rstrip(":")
                self.assertIn(reason, _string_constants(path))

    def test_break_one_character_changed_finds_nothing(self):
        for prefix, reason in log_guard.APPROVED_SKIP_REASONS:
            with self.subTest(prefix=prefix):
                path = prefix.rstrip(":")
                changed = reason[:-1] + ("#" if reason[-1] != "#" else "!")
                self.assertNotEqual(changed, reason)
                self.assertIn(reason, _string_constants(path))
                self.assertNotIn(changed, _string_constants(path))


# --------------------------------------------------------------------------
# Usage, mutants of the guard itself, import lock
# --------------------------------------------------------------------------

class TestUsage(TmpCase):
    def test_unknown_subcommand_exits_2(self):
        self.assertEqual(run_main(["check-everything", LIST_FILE])[0], 2)

    def test_no_arguments_exits_2(self):
        self.assertEqual(run_main([])[0], 2)

    def test_wrong_arity_exits_2(self):
        self.assertEqual(run_main(["check-list"])[0], 2)
        self.assertEqual(run_main(["check-skips", LIST_FILE])[0], 2)

    def test_cli_matches_main(self):
        for argv in (["check-list", LIST_FILE], ["bogus"]):
            proc = subprocess.run([sys.executable, "-I", GUARD_PY, *argv],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=60)
            self.assertEqual(proc.returncode, run_main(argv)[0])


class TestMutants(SkipCase):
    def test_check_list_reads_the_constant(self):
        self.assertEqual(run_main(["check-list", LIST_FILE])[0], 0)
        six = log_guard.RECORDED_FIVE + (REPLAY + "TestCensus::test_census",)
        self.assertNotEqual(six, log_guard.RECORDED_FIVE)
        with mock.patch.object(log_guard, "RECORDED_FIVE", six):
            code, _out, err = run_main(["check-list", LIST_FILE])
        self.assertEqual(code, 1)
        self.assertIn(LIST_STOP, err)

    def test_reason_is_load_bearing_in_the_comparison(self):
        changed = LANE_REASON[:-1] + "E"
        cases = [c if c[2] != LANE_REASON else (c[0], c[1], changed) for c in GOOD_CASES]
        self.assertEqual(self.skips(GOOD_PAIRS, cases)[0], 1)
        with mock.patch.object(log_guard, "_pair_key", lambda pair: pair[0]):
            code, _out, _err = self.skips(GOOD_PAIRS, cases)
        # Ignoring reasons lets the changed-reason mutant through: the reason
        # half of each pair is what the comparison relies on.
        self.assertEqual(code, 0)


class TestImportSet(unittest.TestCase):
    def test_module_level_imports(self):
        with open(GUARD_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertEqual(names, {"re", "sys", "xml"})

    def test_every_subprocess_run_in_tests_has_timeout(self):
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "run"
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"]
        self.assertTrue(calls)
        for c in calls:
            self.assertIn("timeout", {k.arg for k in c.keywords})


if __name__ == "__main__":
    unittest.main()
