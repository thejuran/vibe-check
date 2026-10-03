"""test_batch_card.py — the read-only card helper as executable decisions.

`batch_card.py` numbers the card rows the two prose files render, tags each
row with "pending since pass N" and "your decision went stale", and lists the
owner decisions for REVIEW.md. It never decides open/closed itself (it imports
carry_state for that) and it never writes state.
"""

import ast
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module under test)
import batch_parse  # noqa: E402
import carry_state  # noqa: E402
from test_carry_state import (  # noqa: E402
    ARCH_HASH, BUGS_HASH, F, HA, HB, ba_state, load_fixture, member_ref,
    mk_finding, mk_pass, mk_state, snap, string_key_writes)

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH_CARD_PY = os.path.join(HERE, "batch_card.py")
HC = "c" * 64
HD = "d" * 64
HE = "e" * 64
ALL_REASONS = set(batch_card.REASONS) | set(carry_state.REASONS) | set(
    batch_parse.REASONS)


def run_cli(args, stdin_bytes=b""):
    return subprocess.run([sys.executable, BATCH_CARD_PY] + args,
                          input=stdin_bytes, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=30)


def rows_of(state, mode="fix-loop", head_blobs=None, subset=None):
    doc, reason = batch_card.build_rows(state, mode, head_blobs, subset)
    assert reason is None, reason
    return doc["rows"]


def dismiss(state, h, at_pass=2, reason="False positive", decision="dismiss"):
    out = carry_state.record_decisions(state, {"at_pass": at_pass, "decisions": [
        {"stable_hash": h, "decision": decision, "reason": reason}]})
    assert out is not None
    return out


def ordering_state():
    rows = [
        mk_finding("medium", "persisted", HA, file="app/a.py", line=9),
        mk_finding("critical", "new", HB, file="app/z.py", line=3),
        mk_finding("low", "new", HC, file="app/a.py", line=1),
        mk_finding("warning", "persisted", HD, file="app/a.py", line=20),
    ]
    return mk_state([mk_pass(1, []), mk_pass(2, rows)])


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, obj):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(obj if isinstance(obj, str) else json.dumps(obj))
        return path


# --------------------------------------------------------------------------- #
# rows
# --------------------------------------------------------------------------- #
class TestRows(unittest.TestCase):
    def test_rows_order_and_low_absent(self):
        rows = rows_of(ordering_state())
        self.assertEqual([(r["n"], r["band"], r["file"], r["line"])
                          for r in rows],
                         [(1, "critical", "app/z.py", 3),
                          (2, "warning", "app/a.py", 20),
                          (3, "medium", "app/a.py", 9)])
        self.assertNotIn(HC, [r["stable_hash"] for r in rows])

    def test_rows_tie_break_file_line_none_last_then_hash(self):
        rows = [
            mk_finding("medium", "new", HB, file="b.py", line=1),
            mk_finding("medium", "new", HD, file="a.py", line=None),
            mk_finding("medium", "new", HC, file="a.py", line=5),
            mk_finding("medium", "new", HA, file="a.py", line=5),
        ]
        s = mk_state([mk_pass(1, rows)])
        self.assertEqual([r["stable_hash"] for r in rows_of(s)],
                         [HA, HC, HD, HB])

    def test_rows_at_pass_is_last_pass_number(self):
        doc, _ = batch_card.build_rows(ordering_state(), "fix-loop")
        self.assertEqual(doc["at_pass"], 2)
        self.assertEqual(doc["mode"], "fix-loop")

    def test_rows_fixture_phase45(self):
        doc, _ = batch_card.build_rows(load_fixture(), "fix-loop")
        self.assertEqual(doc["at_pass"], 2)
        self.assertEqual([(r["n"], r["band"], r["stable_hash"])
                          for r in doc["rows"]],
                         [(1, "warning", ARCH_HASH), (2, "medium", BUGS_HASH)])
        # Snapshotless rows: never pending, never stale.
        for r in doc["rows"]:
            self.assertIsNone(r["pending_since"])
            self.assertIsNone(r["stale"])
            self.assertIsInstance(r["problem"], str)
            self.assertTrue(r["problem"])

    def test_rows_closed_by_current_decision_absent(self):
        s = dismiss(ba_state(row_band="warning", a_band="medium"), HA)
        hashes = [r["stable_hash"] for r in rows_of(s)]
        self.assertEqual(hashes, [HB])

    def test_rows_stale_decision_present_with_tag(self):
        decided = dismiss(ba_state(row_band="warning", a_band="medium"), HA,
                          reason="Accepted risk")
        fresh = ba_state(row_band="warning", a_band="warning")
        s = copy.deepcopy(decided)
        s["passes"] = fresh["passes"]
        rows = {r["stable_hash"]: r for r in rows_of(s)}
        self.assertIn(HA, rows)
        self.assertEqual(rows[HA]["stale"], {
            "cause": "severity", "decision": "dismiss",
            "reason": "Accepted risk", "at_pass": 2, "was_band": "medium",
            "via": "same_hash", "prior_hash": HA})
        self.assertIsNone(rows[HB]["stale"])

    def test_rows_stale_line_move_cause_code(self):
        decided = dismiss(ba_state(a_snapshot=snap(1, line=11)), HA)
        s = copy.deepcopy(decided)
        s["passes"] = ba_state(a_snapshot=snap(1, line=14))["passes"]
        rows = {r["stable_hash"]: r for r in rows_of(s)}
        self.assertEqual(rows[HA]["stale"]["cause"], "code")
        self.assertEqual(rows[HA]["stale"]["was_band"], "warning")

    def test_rows_stale_null_evidence_uses_record_band(self):
        s = ba_state(a_band="warning")
        s["decisions"] = {HA: {"decision": "defer", "reason": "r",
                               "at_pass": 1, "band": "medium",
                               "evidence": None}}
        rows = {r["stable_hash"]: r for r in rows_of(s)}
        self.assertEqual(rows[HA]["stale"]["cause"], "code")
        self.assertEqual(rows[HA]["stale"]["was_band"], "medium")
        self.assertEqual(rows[HA]["stale"]["decision"], "defer")

    def test_rows_pending_since(self):
        s = ba_state(a_snapshot=snap(1, line=11))
        rows = {r["stable_hash"]: r for r in rows_of(s)}
        self.assertEqual(rows[HA]["pending_since"], 1)
        self.assertIsNone(rows[HB]["pending_since"])
        s2 = ba_state(a_snapshot=snap(2, line=11))
        rows2 = {r["stable_hash"]: r for r in rows_of(s2)}
        self.assertIsNone(rows2[HA]["pending_since"])

    def test_rows_member_sidecar(self):
        rows = {r["stable_hash"]: r for r in rows_of(ba_state())}
        self.assertEqual(rows[HA]["absorbed_into"], HB)
        self.assertEqual(rows[HA]["lead_title"], rows[HB]["title"])
        self.assertEqual(rows[HA]["problem"], "")
        self.assertIsNone(rows[HB]["absorbed_into"])
        self.assertIsNone(rows[HB]["lead_title"])

    def test_rows_finalize_uses_finalize_counts(self):
        s = load_fixture()
        s["fix_verdicts"] = {ARCH_HASH: {
            "verdict": "obsolete", "agent": "fix", "head_sha": "x",
            "at_pass": 2, "verified_blob": "b1", "reason": ""}}
        arch_file = [f for f in s["passes"][-1]["findings"]
                     if f["stable_hash"] == ARCH_HASH][0]["file"]
        rows = rows_of(s, "finalize", {arch_file: "b1"})
        self.assertEqual([r["stable_hash"] for r in rows], [BUGS_HASH])
        # Without the matching blob the verdict closes nothing.
        rows = rows_of(s, "finalize", {})
        self.assertEqual([r["stable_hash"] for r in rows],
                         [ARCH_HASH, BUGS_HASH])
        counts = carry_state.finalize_counts(s, {})
        self.assertEqual(set(r["stable_hash"] for r in rows),
                         set(counts["outstanding_cw_hashes"]
                             + counts["unacknowledged_medium_hashes"]))

    def test_rows_finalize_cw_before_medium(self):
        rows = rows_of(ordering_state(), "finalize", {})
        self.assertEqual([r["band"] for r in rows],
                         ["critical", "warning", "medium"])

    def test_rows_subset_one_of_three(self):
        rows = rows_of(ordering_state(), "fix-loop", subset=[HD])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["n"], 1)
        self.assertEqual(rows[0]["stable_hash"], HD)
        self.assertFalse(rows[0]["lead_closed"])
        self.assertEqual(rows[0]["routed_members"], [])

    def test_rows_title_problem_are_data(self):
        s = ordering_state()
        s["passes"][-1]["findings"][1]["title"] = "ZZMARKER, \"quote\""
        s["passes"][-1]["findings"][1]["problem"] = 7
        row = rows_of(s)[0]
        self.assertEqual(row["title"], "ZZMARKER, \"quote\"")
        self.assertEqual(row["problem"], "")

    def test_rows_malformed_state(self):
        doc, reason = batch_card.build_rows({"passes": []}, "fix-loop")
        self.assertIsNone(doc)
        self.assertIn(reason, carry_state.REASONS)


# --------------------------------------------------------------------------- #
# decisions-report
# --------------------------------------------------------------------------- #
class TestReport(unittest.TestCase):
    def _state(self):
        s = ba_state(row_band="warning", a_band="medium")
        s = dismiss(s, HB, reason="first")
        s = dismiss(s, HB, reason="second", at_pass=2)
        s = dismiss(s, HA, decision="defer", reason="later")
        # HA's evidence goes stale (band change); HD is an orphan.
        s["passes"][-1]["findings"][0]["members"][1]["obligation"]["band"] = (
            "warning")
        s["passes"][-1]["findings"][0]["members"][1]["obligation"][
            "snapshot"]["band"] = "warning"
        s["decisions"][HD] = {"decision": "dismiss", "reason": "gone",
                              "at_pass": 1, "band": "medium",
                              "evidence": snap(1)}
        return s

    def test_report_classifications(self):
        rep = batch_card.decisions_report(self._state())
        got = [(e["stable_hash"], e["status"], e["reason"])
               for e in rep["entries"]]
        self.assertIn((HB, "current", "second"), got)
        self.assertIn((HB, "superseded", "first"), got)
        self.assertIn((HA, "superseded", "later"), got)
        self.assertIn((HD, "orphan", "gone"), got)
        self.assertEqual(len(got), 4)

    def test_report_joins(self):
        rep = batch_card.decisions_report(self._state())
        by = {(e["stable_hash"], e["status"]): e for e in rep["entries"]}
        self.assertEqual(by[(HA, "superseded")]["title"], "A")
        self.assertEqual(by[(HA, "superseded")]["line"], 11)
        self.assertEqual(by[(HB, "current")]["file"], F)
        orphan = by[(HD, "orphan")]
        for k in ("file", "line", "title", "agent"):
            self.assertIsNone(orphan[k])
        self.assertEqual(orphan["band"], "medium")
        self.assertEqual(orphan["at_pass"], 1)

    def test_report_empty(self):
        self.assertEqual(batch_card.decisions_report(ordering_state()),
                         {"entries": []})

    def test_report_malformed(self):
        self.assertIsNone(batch_card.decisions_report({"passes": 3}))


# --------------------------------------------------------------------------- #
# read-only locks
# --------------------------------------------------------------------------- #
BANNED_KEYS = {"decisions", "fix_verdicts", "passes", "medium_acknowledgments",
               "snapshot"}


def banned_writes(source):
    return [(fn, k) for fn, k in string_key_writes(source) if k in BANNED_KEYS]


class TestReadOnly(unittest.TestCase):
    def _source(self):
        with open(BATCH_CARD_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_no_state_family_writes(self):
        src = self._source()
        self.assertEqual(banned_writes(src), [])
        # Non-vacuity: the walker does see batch_card's own row writes.
        self.assertTrue(string_key_writes(src), "lock is vacuous")

    def test_lock_trips_on_injected_write(self):
        src = self._source()
        anchor = "def decisions_report(state):\n"
        self.assertEqual(src.count(anchor), 1)
        for inject in ('    state["decisions"]["x"] = 1\n',
                       '    state["passes"].append(1)\n',
                       '    rec["snapshot"] = None\n',
                       '    state.setdefault("fix_verdicts", {})\n'):
            with self.subTest(inject=inject):
                mutated = src.replace(anchor, anchor + inject)
                self.assertTrue(banned_writes(mutated))

    def test_import_set(self):
        imported = set()
        for node in ast.walk(ast.parse(self._source())):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(imported <= {"json", "os", "sys", "carry_state",
                                     "batch_parse"}, imported)
        self.assertIn("carry_state", imported)

    def test_no_open_for_write(self):
        for node in ast.walk(ast.parse(self._source())):
            if isinstance(node, ast.Call) and getattr(node.func, "id",
                                                      None) == "open":
                self.fail("batch_card.py must read files via carry_state")

    def test_reasons_fixed_lines(self):
        self.assertIsInstance(batch_card.REASONS, tuple)
        for r in batch_card.REASONS:
            self.assertTrue(r.endswith("\n"))
            self.assertNotIn("%", r)
            self.assertNotIn("{", r)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
class TestCli(TempDirCase):
    def assertRefused(self, proc, reasons=None):
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertIn(proc.stderr.decode(), reasons or ALL_REASONS)

    def test_cli_rows_fixture(self):
        with open(os.path.join(HERE, "fixtures", "phase45-loop-state.json"),
                  "rb") as fh:
            data = fh.read()
        proc = run_cli(["rows", "--mode", "fix-loop"], data)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        doc = json.loads(proc.stdout.decode())
        self.assertEqual((doc["at_pass"], [(r["n"], r["band"])
                                           for r in doc["rows"]]),
                         (2, [(1, "warning"), (2, "medium")]))
        again = run_cli(["rows", "--mode", "fix-loop"], data)
        self.assertEqual(proc.stdout, again.stdout)

    def test_cli_rows_finalize_with_blobs(self):
        blobs = self.write("blobs.json", {})
        proc = run_cli(["rows", "--mode", "finalize", "--head-blobs", blobs],
                       json.dumps(ordering_state()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(len(json.loads(proc.stdout)["rows"]), 3)

    def test_cli_finalize_requires_head_blobs(self):
        proc = run_cli(["rows", "--mode", "finalize"],
                       json.dumps(ordering_state()).encode())
        self.assertRefused(proc, {batch_card.USAGE})

    def test_cli_bad_head_blobs(self):
        for name, content in (("list", [1]), ("num", {"a": 1}),
                              ("text", "not json")):
            with self.subTest(name):
                path = self.write(name + ".json", content)
                proc = run_cli(["rows", "--mode", "finalize", "--head-blobs",
                                path], json.dumps(ordering_state()).encode())
                self.assertRefused(proc, {batch_card.REASON_HEAD_BLOBS})

    def test_cli_bad_subset(self):
        for name, content in (("obj", {"a": 1}), ("nums", [1]),
                              ("text", "nope")):
            with self.subTest(name):
                path = self.write(name + ".json", content)
                proc = run_cli(["rows", "--mode", "fix-loop", "--subset",
                                path], json.dumps(ordering_state()).encode())
                self.assertRefused(proc, {batch_card.REASON_SUBSET})

    def test_cli_malformed_state(self):
        proc = run_cli(["rows", "--mode", "fix-loop"], b"not json")
        self.assertRefused(proc, {batch_card.REASON_STATE_JSON})
        for state in ({"passes": []}, {"passes": [{"pass_number": 1}]}, [1]):
            with self.subTest(state=state):
                for argv in (["rows", "--mode", "fix-loop"],
                             ["decisions-report"]):
                    proc = run_cli(argv, json.dumps(state).encode())
                    self.assertRefused(proc, set(carry_state.REASONS))

    def test_cli_usage_errors(self):
        state = json.dumps(ordering_state()).encode()
        for argv in ([], ["bogus"], ["rows"], ["rows", "--mode"],
                     ["rows", "--mode", "sideways"],
                     ["rows", "--mode", "fix-loop", "--title", "x"],
                     ["rows", "--mode", "fix-loop", "--mode", "fix-loop"],
                     ["rows", "--mode", "fix-loop", "--head-blobs", "x"],
                     ["rows", "--mode", "finalize", "--head-blobs", "x",
                      "--subset", "y"],
                     ["decisions-report", "--mode", "fix-loop"]):
            with self.subTest(argv=argv):
                self.assertRefused(run_cli(argv, state), {batch_card.USAGE})

    def test_cli_decisions_report(self):
        s = dismiss(ba_state(), HA)
        proc = run_cli(["decisions-report"], json.dumps(s).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout),
                         batch_card.decisions_report(s))


if __name__ == "__main__":
    unittest.main()
