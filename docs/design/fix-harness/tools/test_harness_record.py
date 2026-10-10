"""Tests for harness_record: a FLOW-05 run record cannot overstate what a
scripted run proves — no fabricated owner-waiting time, no missing label, no
COMPLETE with the sandbox off or escapable, and no COMPLETE that lost,
downgraded or regressed an obligation or hid a retained-open one.

Run with bare `pytest -q` from this directory.
"""

import copy as copymod
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_record as hr  # noqa: E402

N4 = "4" * 64


def obligations(**over):
    o = {"tracked": 3, "snapshots": 4, "resolved": 1, "fix_verified": 0,
         "decided": 1, "visible_open_nonblocking": 1,
         "visible_open_nonblocking_hashes": [N4], "downgraded": 0,
         "regression": 0, "missing": 0, "ambiguous": 0}
    o.update(over)
    return o


def containment(**over):
    c = {"sandbox_enabled": True, "fail_if_unavailable": True,
         "unsandboxed_retry": False, "probe_fingerprint": "f" * 64,
         "denials": 2, "protected_path_denials": 0}
    c.update(over)
    return c


def kwargs(**over):
    k = dict(
        case_id="py-clamp-01", mode="default", kind="preservation",
        entry="review", plugin_path="/ws/plugin-snapshot",
        plugin_source_path="/Users/me/repo/plugins/vibe-check",
        plugin_sha="a" * 40, plugin_snapshot_sha256="b" * 64,
        plugin_tree_dirty=False, copy_root="/ws/repo", cli_version="2.1.0",
        model="claude-opus-5-5", setting_sources=[],
        decisions={"cards": 3, "questions": 2, "turn_end_questions": 1,
                   "owner_commands": 1, "repeats": 1,
                   "deferred_non_seeded": 1},
        execution_seconds=123.4, harness_answer_seconds=0.5,
        clean_tree_checkpoint=None, containment=containment(),
        obligations=obligations(), verdict="COMPLETE", reasons=[],
        transcript_sha256="c" * 64)
    k.update(over)
    return k


class TestBuild(unittest.TestCase):
    def test_constant_fields_are_filled_by_the_builder(self):
        r = hr.build_record(**kwargs())
        self.assertIsNone(r["waiting_on_owner_seconds"])
        self.assertEqual(r["waiting_on_owner_note"],
                         "not measured — scripted run, no human in the loop")
        self.assertEqual(r["execution_seconds_label"],
                         "automated execution time")
        self.assertEqual(r["would_be_owner_questions"], 2 + 1 + 1)
        self.assertEqual(hr.validate_record(r), [])

    def test_callers_cannot_set_the_constant_fields(self):
        for field in ("waiting_on_owner_seconds", "waiting_on_owner_note",
                      "execution_seconds_label", "would_be_owner_questions"):
            with self.subTest(field), self.assertRaises(TypeError):
                hr.build_record(**kwargs(**{field: 1}))

    def test_positional_arguments_are_refused(self):
        with self.assertRaises(TypeError):
            hr.build_record("py-clamp-01")

    def test_containment_and_obligations_are_never_defaulted(self):
        for field in ("containment", "obligations"):
            k = kwargs()
            del k[field]
            with self.subTest(field), self.assertRaises(TypeError):
                hr.build_record(**k)
            r = hr.build_record(**kwargs(**{field: None}))
            self.assertTrue(hr.validate_record(r))

    def test_round_trip_through_write(self):
        r = hr.build_record(**kwargs())
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "run.json")
            hr.write_record(path, r)
            with open(path, "r", encoding="utf-8") as fh:
                self.assertEqual(json.load(fh), r)
            self.assertEqual(os.listdir(d), ["run.json"])


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.good = hr.build_record(**kwargs())

    def bad(self, mutate):
        r = copymod.deepcopy(self.good)
        mutate(r)
        problems = hr.validate_record(r)
        self.assertTrue(problems, "a bad record was accepted")
        return problems

    def test_missing_key(self):
        for key in hr.REQUIRED_KEYS:
            with self.subTest(key):
                self.bad(lambda r: r.pop(key))

    def test_d13_waiting_on_owner_lock(self):
        for value in (12.5, 0, 0.0, "0"):
            with self.subTest(value):
                self.bad(lambda r: r.__setitem__("waiting_on_owner_seconds",
                                                 value))
        self.bad(lambda r: r.__setitem__("waiting_on_owner_note", "n/a"))
        self.bad(lambda r: r.__setitem__("execution_seconds_label",
                                         "time saved"))

    def test_question_sum(self):
        self.bad(lambda r: r.__setitem__("would_be_owner_questions", 3))
        self.bad(lambda r: r["decisions"].pop("repeats"))

    def test_containment_lock(self):
        cases = {
            "sandbox off": {"sandbox_enabled": False},
            "fail open": {"fail_if_unavailable": False},
            "retry allowed": {"unsandboxed_retry": True},
            "truthy not True": {"sandbox_enabled": 1},
            "denials not int": {"denials": "2"},
        }
        for name, over in cases.items():
            with self.subTest(name):
                self.bad(lambda r: r["containment"].update(over))
        self.bad(lambda r: r.__setitem__("containment", None))

    def test_protected_path_denial_blocks_complete_only(self):
        self.bad(lambda r: r["containment"].update(protected_path_denials=1))
        r = copymod.deepcopy(self.good)
        r["containment"]["protected_path_denials"] = 1
        r["verdict"] = "FAILED"
        r["reasons"] = ["head check sandbox unavailable: not darwin"]
        self.assertEqual(hr.validate_record(r), [])

    def test_obligations_lock(self):
        cases = {
            "missing on COMPLETE": {"missing": 1, "tracked": 4},
            "ambiguous on COMPLETE": {"ambiguous": 1, "tracked": 4},
            "downgraded on COMPLETE": {"downgraded": 1, "tracked": 4},
            "regression on COMPLETE": {"regression": 1, "tracked": 4},
            "sum mismatch": {"tracked": 4},
            "tracked zero": {"tracked": 0, "resolved": 0, "decided": 0,
                             "visible_open_nonblocking": 0,
                             "visible_open_nonblocking_hashes": []},
            "one snapshot": {"snapshots": 1},
            "negative": {"resolved": -1, "tracked": 1},
            "bool count": {"fix_verified": True, "tracked": 4},
            "count without list": {"visible_open_nonblocking_hashes": []},
            "list without count": {"visible_open_nonblocking": 0,
                                   "tracked": 2},
            "unsorted list": {"visible_open_nonblocking": 2, "tracked": 4,
                              "visible_open_nonblocking_hashes":
                                  ["b" * 64, "a" * 64]},
            "duplicate list": {"visible_open_nonblocking": 2, "tracked": 4,
                               "visible_open_nonblocking_hashes":
                                   [N4, N4]},
        }
        for name, over in cases.items():
            with self.subTest(name):
                self.bad(lambda r: r["obligations"].update(over))
        for key in hr.OBLIGATION_KEYS:
            with self.subTest("drop " + key):
                self.bad(lambda r: r["obligations"].pop(key))
        self.bad(lambda r: r.__setitem__("obligations", None))

    def test_failed_record_may_carry_lost_obligations(self):
        r = copymod.deepcopy(self.good)
        r["obligations"].update(missing=1, tracked=4)
        r["verdict"] = "FAILED"
        r["reasons"] = ["obligation dropped without decision: 1234567"]
        self.assertEqual(hr.validate_record(r), [])

    def test_copy_inside_the_checkout_is_refused(self):
        self.bad(lambda r: r.__setitem__("copy_root",
                                         "/Users/me/repo/work/repo"))
        self.bad(lambda r: r.__setitem__("copy_root", "/Users/me/repo"))
        r = copymod.deepcopy(self.good)
        r["copy_root"] = "/Users/me/repository-copies/repo"
        self.assertEqual(hr.validate_record(r), [])

    def test_verdict_and_reasons_agree(self):
        self.bad(lambda r: r.__setitem__("verdict", "PASSED"))
        self.bad(lambda r: r.__setitem__("reasons", ["x"]))
        self.bad(lambda r: (r.__setitem__("verdict", "FAILED"),
                            r.__setitem__("reasons", [])))


class TestWrite(unittest.TestCase):
    def test_refusal_leaves_nothing(self):
        r = hr.build_record(**kwargs())
        r["waiting_on_owner_seconds"] = 12.5
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "run.json")
            with self.assertRaises(hr.RecordError):
                hr.write_record(path, r)
            self.assertEqual(os.listdir(d), [])

    def _writes(self, record):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "run.json")
            try:
                hr.write_record(path, record)
            except hr.RecordError:
                return False
            return os.path.exists(path)

    def test_m1_d13_mutant(self):
        r = hr.build_record(**kwargs())
        r["waiting_on_owner_seconds"] = 12.5
        self.assertFalse(self._writes(r))
        with mock.patch.object(hr, "_timing_problems", lambda r: []):
            self.assertTrue(self._writes(r))

    def test_m2_containment_mutant(self):
        off = hr.build_record(**kwargs(containment=containment(
            sandbox_enabled=False)))
        denied = hr.build_record(**kwargs(containment=containment(
            protected_path_denials=1)))
        for r in (off, denied):
            self.assertFalse(self._writes(r))
            with mock.patch.object(hr, "_containment_problems",
                                   lambda r: []):
                self.assertTrue(self._writes(r))

    def test_m3_obligations_mutant(self):
        shapes = {
            "missing": obligations(missing=1, tracked=4),
            "one snapshot": obligations(snapshots=1),
            "downgraded": obligations(downgraded=1, tracked=4),
            "regression": obligations(regression=1, tracked=4),
            "count disagrees with list": obligations(
                visible_open_nonblocking=0, tracked=2),
        }
        for name, o in shapes.items():
            with self.subTest(name):
                r = hr.build_record(**kwargs(obligations=o))
                self.assertFalse(self._writes(r))
                with mock.patch.object(hr, "_obligation_problems",
                                       lambda r: []):
                    self.assertTrue(self._writes(r))


if __name__ == "__main__":
    unittest.main()
