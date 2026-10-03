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
import finalize_gate  # noqa: E402
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


# --------------------------------------------------------------------------- #
# Answer side: select-questions, select, parse, payload, fix routing.
# --------------------------------------------------------------------------- #
LABEL_RE = r"^#\d+ \S+:(\d+|\?)$"
LEAD_TITLE = "LEADTITLE lead defect"
LEAD_PROBLEM = "LEADPROBLEM the lead's own defect"
LEAD_CODE = "lead_code_LEADCODE()"


def synth_rows(count, at_pass=2):
    bands = ("critical", "warning", "medium")
    return {"at_pass": at_pass, "mode": "fix-loop", "rows": [
        {"n": i + 1, "stable_hash": "%064x" % (i + 1),
         "band": bands[i % 3], "file": "app/f%d.py" % i, "line": i + 1,
         "title": "title %d" % i, "problem": "problem %d " % i + "x" * 100}
        for i in range(count)]}


def dispatch_state():
    """ba_state with real defect text on the lead HB and its member HA."""
    s = ba_state(row_band="warning", a_band="medium")
    lead = s["passes"][-1]["findings"][0]
    lead.update(title=LEAD_TITLE, problem=LEAD_PROBLEM,
                current_code=LEAD_CODE, fix_hint="LEADHINT",
                why_it_matters="LEADWHY")
    member = lead["members"][1]
    member.update(problem="MEMBERPROBLEM", current_code="member_code()",
                  fix_hint="MEMBERHINT", why_it_matters="MEMBERWHY")
    return s


def member_unit():
    return {"id": HA, "file": F, "line": 11, "title": "A",
            "problem": "MEMBERPROBLEM", "current_code": "member_code()",
            "fix_hint": "MEMBERHINT", "why_it_matters": "MEMBERWHY"}


class TestSelectQuestions(unittest.TestCase):
    def sizes(self, count):
        out = batch_card.select_questions(synth_rows(count)["rows"])
        return out["mode"], [len(q["options"]) for q in out["questions"]]

    def test_balanced_split(self):
        self.assertEqual(self.sizes(1), ("none", []))
        self.assertEqual(self.sizes(0), ("none", []))
        self.assertEqual(self.sizes(2), ("multiselect", [2]))
        self.assertEqual(self.sizes(4), ("multiselect", [4]))
        self.assertEqual(self.sizes(5), ("multiselect", [3, 2]))
        self.assertEqual(self.sizes(6), ("multiselect", [3, 3]))
        self.assertEqual(self.sizes(7), ("multiselect", [4, 3]))
        self.assertEqual(self.sizes(9), ("multiselect", [3, 3, 3]))
        self.assertEqual(self.sizes(13), ("multiselect", [4, 3, 3, 3]))
        self.assertEqual(self.sizes(16), ("multiselect", [4, 4, 4, 4]))

    def test_every_shape_legal(self):
        for count in range(2, 17):
            with self.subTest(count=count):
                out = batch_card.select_questions(synth_rows(count)["rows"])
                self.assertLessEqual(len(out["questions"]), 4)
                labels = []
                for q in out["questions"]:
                    self.assertTrue(q["multiSelect"])
                    self.assertLessEqual(len(q["header"]), 12)
                    self.assertTrue(2 <= len(q["options"]) <= 4)
                    for opt in q["options"]:
                        self.assertRegex(opt["label"], LABEL_RE)
                        self.assertNotIn(",", opt["label"])
                        labels.append(opt["label"])
                self.assertEqual([int(lb.split()[0][1:]) for lb in labels],
                                 list(range(1, count + 1)))

    def test_typed_over_sixteen(self):
        out = batch_card.select_questions(synth_rows(17)["rows"])
        self.assertEqual(out["mode"], "typed")
        self.assertEqual(len(out["questions"]), 1)
        q = out["questions"][0]
        self.assertEqual([o["label"] for o in q["options"]],
                         ["All listed", "None — skip & rerun"])
        self.assertIn("Other", q["question"])
        self.assertLessEqual(len(q["header"]), 12)

    def test_label_sanitized_description_carries_title(self):
        rows = synth_rows(2)["rows"]
        rows[0]["file"] = "dir with space/a,b.py"
        rows[0]["line"] = None
        rows[0]["title"] = "Title, with comma"
        out = batch_card.select_questions(rows)
        opt = out["questions"][0]["options"][0]
        self.assertRegex(opt["label"], LABEL_RE)
        self.assertNotIn(",", opt["label"])
        self.assertTrue(opt["label"].startswith("#1 "))
        self.assertTrue(opt["label"].endswith(":?"))
        self.assertTrue(opt["description"].startswith("Title, with comma — "))
        self.assertLessEqual(len(opt["description"]),
                             len("Title, with comma — ") + 80)


class TestSelect(TempDirCase):
    def setUp(self):
        super().setUp()
        self.rows = batch_card.build_rows(ordering_state(), "fix-loop")[0]
        self.rows_path = self.write("rows.json", self.rows)

    def sel(self, answer):
        return run_cli(["select", "--rows", self.rows_path, "--answer",
                        self.write("ans.json", answer)])

    def test_select_shapes(self):
        h = [r["stable_hash"] for r in self.rows["rows"]]
        cases = [({"labels": ["#2 app/a.py:20", "#3 app/a.py:9"]}, [2, 3]),
                 ({"labels": "#2 app/a.py:20, #3 app/a.py:9"}, [2, 3]),
                 ({"text": "1,3"}, [1, 3]),
                 ({"all": True}, [1, 2, 3]),
                 ({"none": True}, [])]
        for answer, want in cases:
            with self.subTest(answer=answer):
                proc = self.sel(answer)
                self.assertEqual(proc.returncode, 0, proc.stderr.decode())
                self.assertEqual(json.loads(proc.stdout),
                                 {"rows": want,
                                  "hashes": [h[n - 1] for n in want]})

    def test_select_bad_label(self):
        proc = self.sel({"labels": ["Fix it ZZMARKER"]})
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr.decode(), batch_parse.REASON_LABEL)

    def test_select_malformed_answer(self):
        for answer in ([1], {"bogus": 1}, {"all": False}, {"none": "yes"},
                       {"labels": ["#1 a"], "text": "1"}, {"text": 3}, {},
                       "not json"):
            with self.subTest(answer=answer):
                proc = self.sel(answer)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(proc.stderr.decode(), batch_card.REASON_ANSWER)
        proc = run_cli(["select", "--rows", self.rows_path, "--answer",
                        os.path.join(self.tmp, "missing.json")])
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_ANSWER)

    def test_malformed_rows_file(self):
        ans = self.write("ans.json", {"all": True})
        bad_rows = copy.deepcopy(self.rows)
        bad_rows["rows"][1]["n"] = 7
        for name, content in (("gap", bad_rows), ("text", "nope"),
                              ("list", [1]), ("norows", {"at_pass": 2}),
                              ("noat", {"rows": []})):
            with self.subTest(name):
                path = self.write(name + ".json", content)
                for sub in ("select", "parse", "select-questions"):
                    argv = [sub, "--rows", path]
                    if sub != "select-questions":
                        argv += ["--answer", ans]
                    proc = run_cli(argv)
                    self.assertEqual(proc.returncode, 2)
                    self.assertEqual(proc.stdout, b"")
                    self.assertEqual(proc.stderr.decode(),
                                     batch_card.REASON_ROWS)


class TestParse(TempDirCase):
    def setUp(self):
        super().setUp()
        self.state = ordering_state()
        self.rows = batch_card.build_rows(self.state, "fix-loop")[0]
        self.rows_path = self.write("rows.json", self.rows)
        # n1 critical HB, n2 warning HD, n3 medium HA

    def parse(self, answer, rows_path=None):
        return run_cli(["parse", "--rows", rows_path or self.rows_path,
                        "--answer", self.write("ans.json", answer)])

    def ok(self, answer, rows_path=None):
        proc = self.parse(answer, rows_path)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        return json.loads(proc.stdout)

    def test_parse_mixed(self):
        out = self.ok({"q1": "fix 2; dismiss rest", "q2": "False positive"})
        self.assertEqual(out["fix"], [HD])
        self.assertEqual(out["dismiss"], [HA])
        self.assertEqual(out["undecided"], [HB])
        self.assertEqual(out["payload"], {"at_pass": 2, "decisions": [
            {"stable_hash": HA, "decision": "dismiss",
             "reason": "False positive"}]})
        self.assertEqual(out["fix_targets"], [HD])

    def test_parse_dismiss_then_defer_row_order(self):
        out = self.ok({"q1": "defer 1; dismiss 3,2", "q2": "Accepted risk"})
        self.assertEqual([(d["stable_hash"], d["decision"])
                          for d in out["payload"]["decisions"]],
                         [(HD, "dismiss"), (HA, "dismiss"), (HB, "defer")])

    def test_parse_round_trip_record_decisions(self):
        out = self.ok({"q1": "fix 2; dismiss rest", "q2": "False positive"})
        new = carry_state.record_decisions(self.state, out["payload"])
        self.assertIsNotNone(new)
        rec = [r for r in carry_state.open_findings(self.state)
               if r["stable_hash"] == HA][0]
        self.assertEqual(new["decisions"][HA]["evidence"],
                         carry_state._evidence_of(rec))

    def test_parse_round_trip_snapshotless_fixture(self):
        state = load_fixture()
        rows = batch_card.build_rows(state, "fix-loop")[0]
        out = self.ok({"q1": "dismiss 1,2", "q2": "Out of scope"},
                      self.write("fx.json", rows))
        new = carry_state.record_decisions(state, out["payload"])
        self.assertIsNotNone(new)
        for h in (ARCH_HASH, BUGS_HASH):
            row = [f for f in state["passes"][-1]["findings"]
                   if f["stable_hash"] == h][0]
            ev = new["decisions"][h]["evidence"]
            self.assertIsNotNone(ev)
            self.assertEqual(ev, {k: row[k] for k in carry_state.EVIDENCE_KEYS})

    def test_parse_fix_all_and_look(self):
        out = self.ok({"q1": "Fix all", "q2": None})
        self.assertIsNone(out["payload"])
        self.assertEqual(out["fix_targets"], [HB, HD, HA])
        out = self.ok({"q1": "look 2"})
        self.assertEqual(out["look"], 2)
        self.assertIsNone(out["payload"])
        self.assertEqual(out["fix_targets"], [])
        out = self.ok({"q1": "Mixed…", "q2": None})
        self.assertTrue(out["need_text"])
        self.assertIsNone(out["payload"])

    def test_parse_grammar_refusal(self):
        proc = self.parse({"q1": "zap 1", "q2": None})
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr.decode(), batch_parse.REASON_TOKEN)

    def test_no_refusal_echoes_owner_text(self):
        for answer in ({"q1": "zap ZZMARKER", "q2": "ZZMARKER"},
                       {"q1": "dismiss 1", "q2": "  "},
                       {"q1": "ZZMARKER"}, {"q1": 5, "q2": "ZZMARKER"},
                       {"q1": "fix 9 ZZMARKER"}):
            with self.subTest(answer=answer):
                proc = self.parse(answer)
                self.assertEqual(proc.returncode, 2)
                self.assertNotIn("ZZMARKER", proc.stderr.decode())
                self.assertIn(proc.stderr.decode(), ALL_REASONS)

    def test_parse_malformed_answer(self):
        for answer in ([1], {"q2": "x"}, {"q1": "fix 1", "extra": 1},
                       {"q1": 3}, {"q1": "fix 1", "q2": 4}):
            with self.subTest(answer=answer):
                proc = self.parse(answer)
                self.assertEqual(proc.stderr.decode(), batch_card.REASON_ANSWER)
                self.assertEqual(proc.stdout, b"")

    def test_fix_targets_owner_chosen_only(self):
        hl, hm1, hm2, h1 = HB, HA, HC, HD
        rows = {"at_pass": 2, "mode": "finalize", "rows": [
            {"n": 1, "stable_hash": h1, "band": "warning", "file": "a.py",
             "line": 1, "absorbed_into": None},
            {"n": 2, "stable_hash": hm1, "band": "medium", "file": "a.py",
             "line": 2, "absorbed_into": hl},
            {"n": 3, "stable_hash": hm2, "band": "medium", "file": "a.py",
             "line": 3, "absorbed_into": hl}]}
        path = self.write("mrows.json", rows)
        self.assertEqual(self.ok({"q1": "fix 1,2"}, path)["fix_targets"],
                         [h1, hm1])
        self.assertEqual(self.ok({"q1": "fix 2,3"}, path)["fix_targets"],
                         [hm1, hm2])
        self.assertEqual(self.ok({"q1": "dismiss 1", "q2": "r"},
                                 path)["fix_targets"], [])


class TestFixRouting(TempDirCase):
    def test_lead_and_member_selected(self):
        s = dismiss(dispatch_state(), HB)
        rows = rows_of(s, "fix-loop", subset=[HB, HA])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["stable_hash"], HB)
        self.assertEqual(rows[0]["n"], 1)
        self.assertTrue(rows[0]["lead_closed"])
        self.assertTrue(rows[0]["lead_selected"])
        self.assertEqual(rows[0]["routed_members"],
                         [{"stable_hash": HA, "title": "A"}])

    def test_member_alone_folds_into_lead(self):
        s = dismiss(dispatch_state(), HB)
        rows = rows_of(s, "fix-loop", subset=[HA])
        self.assertEqual([r["stable_hash"] for r in rows], [HB])
        self.assertFalse(rows[0]["lead_selected"])
        self.assertTrue(rows[0]["lead_closed"])
        self.assertEqual(rows[0]["routed_members"][0]["stable_hash"], HA)

    def test_member_before_lead_then_lead(self):
        rows = rows_of(dispatch_state(), "fix-loop", subset=[HA, HB, HA])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["lead_selected"])
        self.assertFalse(rows[0]["lead_closed"])
        self.assertEqual(len(rows[0]["routed_members"]), 1)

    def test_unknown_hash_dropped_and_all_unknown_refused(self):
        rows = rows_of(ordering_state(), "fix-loop", subset=["deadbeef", HD])
        self.assertEqual([r["stable_hash"] for r in rows], [HD])
        path = self.write("sub.json", ["deadbeef"])
        proc = run_cli(["rows", "--mode", "fix-loop", "--subset", path],
                       json.dumps(ordering_state()).encode())
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_SUBSET_EMPTY)

    def test_subset_keeps_verified_obsolete_target(self):
        s = ordering_state()
        s["fix_verdicts"] = {HD: {"verdict": "obsolete", "agent": "fix",
                                  "head_sha": "x", "at_pass": 2,
                                  "verified_blob": "b1", "reason": ""}}
        self.assertTrue(carry_state.is_closed(
            [r for r in carry_state.open_findings(s)
             if r["stable_hash"] == HD][0], s, {"app/a.py": "b1"}))
        rows = rows_of(s, "fix-loop", subset=[HD])
        self.assertEqual([r["stable_hash"] for r in rows], [HD])


# --- the dismiss-lead / fix-member case, end to end ------------------------ #
def check_subset_rows(test, rows):
    test.assertEqual(len(rows), 1)
    row = rows[0]
    test.assertEqual(row["stable_hash"], HB)
    test.assertTrue(row["lead_closed"])
    test.assertFalse(row["lead_selected"])
    test.assertEqual(row["routed_members"][0]["stable_hash"], HA)


def check_member_only(test, out):
    test.assertEqual(out["sent"], [HA])
    test.assertEqual(out["findings"], [member_unit()])
    test.assertNotIn(HB, [f["id"] for f in out["findings"]])
    blob = json.dumps(out["findings"])
    for lead_text in (LEAD_TITLE, LEAD_PROBLEM, LEAD_CODE):
        test.assertNotIn(lead_text, blob)


class TestDismissLeadFixMember(TempDirCase):
    def decided(self):
        return dismiss(dispatch_state(), HB, reason="False positive")

    def test_dismiss_lead_fix_member_integration(self):
        # (1) the owner dismissed the lead by number.
        state = self.decided()
        before = json.dumps(state["decisions"][HB], sort_keys=True)
        state_bytes = json.dumps(state).encode()
        # (2) finalize rows: the member is the one undecided row.
        blobs = self.write("blobs.json", {})
        proc = run_cli(["rows", "--mode", "finalize", "--head-blobs", blobs],
                       state_bytes)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        frows = json.loads(proc.stdout)
        self.assertEqual([(r["stable_hash"], r["absorbed_into"])
                          for r in frows["rows"]], [(HA, HB)])
        frows_path = self.write("frows.json", frows)
        # (3) the owner chooses fix on the member.
        proc = run_cli(["parse", "--rows", frows_path, "--answer",
                        self.write("ans.json", {"q1": "fix 1", "q2": None})])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        parsed = json.loads(proc.stdout)
        self.assertEqual(parsed["fix"], [HA])
        self.assertIsNone(parsed["payload"])
        self.assertEqual(parsed["fix_targets"], [HA])
        # (4) fix-loop rows for the subset route through the closed lead.
        subset = self.write("subset.json", parsed["fix_targets"])
        proc = run_cli(["rows", "--mode", "fix-loop", "--subset", subset],
                       state_bytes)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        srows = json.loads(proc.stdout)
        check_subset_rows(self, srows["rows"])
        # (5) the dispatch carries the member's own defect only.
        proc = run_cli(["payload", "--rows", self.write("srows.json", srows),
                        "--answer", self.write("all.json", {"all": True})],
                       state_bytes)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout)
        check_member_only(self, out)
        # (6) the lead's decision was never reopened or rewritten.
        self.assertEqual(json.dumps(state["decisions"][HB], sort_keys=True),
                         before)
        # (7) the member id is a valid verdict target; nothing for the lead.
        new = carry_state.record_fix_verdicts(state, {
            "at_pass": 2, "head_sha": "h2", "sent": out["sent"],
            "results": [{"id": HA, "status": "obsolete", "summary": "gone"},
                        {"id": HB, "status": "obsolete", "summary": "x"}],
            "blobs": {F: "blob1"}})
        self.assertIsNotNone(new)
        self.assertIn(HA, new["fix_verdicts"])
        self.assertNotIn(HB, new["fix_verdicts"])
        self.assertEqual(new["decisions"][HB], state["decisions"][HB])

    def test_dismiss_lead_fix_member_mutation(self):
        state = self.decided()
        real = batch_card.resolve_fix_targets

        def filtering(st, subset):
            recs = {r["stable_hash"]: r for r in carry_state.open_findings(st)}
            return [r for r in real(st, subset)
                    if not carry_state.is_closed(recs[r["stable_hash"]], st,
                                                 None)]

        with self.subTest("real"):
            check_subset_rows(self, rows_of(state, "fix-loop", subset=[HA]))
        with self.subTest("mutant"):
            with mock.patch.object(batch_card, "resolve_fix_targets",
                                   filtering):
                doc, _reason = batch_card.build_rows(state, "fix-loop", None,
                                                     [HA])
            rows = doc["rows"] if doc else []
            self.assertEqual(rows, [])
            with self.assertRaises(AssertionError):
                check_subset_rows(self, rows)

    def _payload_in_process(self, state):
        srows = batch_card.build_rows(state, "fix-loop", None, [HA])[0]
        code, out = batch_card.run(
            ["payload", "--rows", self.write("srows.json", srows),
             "--answer", self.write("all.json", {"all": True})],
            json.dumps(state))
        self.assertEqual(code, 0)
        return json.loads(out)

    def test_dismiss_lead_payload_mutation(self):
        state = self.decided()
        real = batch_card.build_payload

        def lead_always(st, rows_doc, answer):
            doc = copy.deepcopy(rows_doc)
            for row in doc["rows"]:
                if "lead_selected" in row:
                    row["lead_selected"] = True
            return real(st, doc, answer)

        with self.subTest("real"):
            check_member_only(self, self._payload_in_process(state))
        with self.subTest("mutant"):
            with mock.patch.object(batch_card, "build_payload", lead_always):
                out = self._payload_in_process(state)
            self.assertIn(HB, out["sent"])
            with self.assertRaises(AssertionError):
                check_member_only(self, out)


class TestPayload(TempDirCase):
    def payload(self, state, rows_doc, answer):
        return run_cli(["payload", "--rows", self.write("r.json", rows_doc),
                        "--answer", self.write("a.json", answer)],
                       json.dumps(state).encode())

    def test_payload_lead_selected_emits_both(self):
        s = dispatch_state()
        srows = batch_card.build_rows(s, "fix-loop", None, [HB, HA])[0]
        proc = self.payload(s, srows, {"all": True})
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout)
        self.assertEqual(out["sent"], [HB, HA])
        self.assertEqual([f["id"] for f in out["findings"]], [HB, HA])
        self.assertEqual(out["findings"][0], {
            "id": HB, "file": F, "line": 10, "title": LEAD_TITLE,
            "problem": LEAD_PROBLEM, "current_code": LEAD_CODE,
            "fix_hint": "LEADHINT", "why_it_matters": "LEADWHY"})
        self.assertEqual(out["findings"][1], member_unit())

    def test_payload_member_sidecar_row_plain_loop(self):
        s = dispatch_state()
        rows = batch_card.build_rows(s, "fix-loop")[0]
        self.assertEqual([(r["n"], r["stable_hash"]) for r in rows["rows"]],
                         [(1, HB), (2, HA)])
        proc = self.payload(s, rows, {"text": "2"})
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout)
        self.assertEqual(out["sent"], [HA])
        self.assertEqual(out["findings"], [member_unit()])
        self.assertEqual(out["findings"][0]["current_code"], "member_code()")
        self.assertEqual(out["findings"][0]["fix_hint"], "MEMBERHINT")

    def test_payload_fields_from_state_not_rows_file(self):
        s = dispatch_state()
        rows = batch_card.build_rows(s, "fix-loop")[0]
        rows["rows"][0]["title"] = "FORGED"
        rows["rows"][0]["problem"] = "FORGED"
        out = json.loads(self.payload(s, rows, {"text": "1"}).stdout)
        self.assertEqual(out["findings"][0]["title"], LEAD_TITLE)
        self.assertNotIn("FORGED", json.dumps(out))

    def test_payload_non_str_fields_normalized(self):
        s = dispatch_state()
        lead = s["passes"][-1]["findings"][0]
        lead.update(problem=None, current_code=3, why_it_matters=[],
                    fix_hint=5)
        rows = batch_card.build_rows(s, "fix-loop")[0]
        out = json.loads(self.payload(s, rows, {"text": "1"}).stdout)
        unit = out["findings"][0]
        self.assertEqual((unit["problem"], unit["current_code"],
                          unit["why_it_matters"], unit["fix_hint"]),
                         ("", "", "", None))

    def test_payload_none_selected(self):
        s = dispatch_state()
        rows = batch_card.build_rows(s, "fix-loop")[0]
        out = json.loads(self.payload(s, rows, {"none": True}).stdout)
        self.assertEqual(out, {"sent": [], "findings": []})

    def test_payload_refuses_mismatched_rows(self):
        s = dispatch_state()
        rows = batch_card.build_rows(s, "fix-loop")[0]
        stale_pass = dict(rows, at_pass=1)
        forged = copy.deepcopy(rows)
        forged["rows"][0]["stable_hash"] = "f" * 64
        routed = batch_card.build_rows(s, "fix-loop", None, [HA])[0]
        routed["rows"][0]["routed_members"] = [{"stable_hash": HC,
                                                "title": "x"}]
        for name, doc in (("at_pass", stale_pass), ("hash", forged),
                          ("routed member", routed)):
            with self.subTest(name):
                proc = self.payload(s, doc, {"all": True})
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(proc.stderr.decode(),
                                 batch_card.REASON_ROWS_STATE)

    def test_payload_refuses_bad_answer_and_state(self):
        s = dispatch_state()
        rows = batch_card.build_rows(s, "fix-loop")[0]
        proc = self.payload(s, rows, {"q1": "fix 1"})
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_ANSWER)
        proc = run_cli(["payload", "--rows", self.write("r.json", rows),
                        "--answer", self.write("a.json", {"all": True})],
                       b"not json")
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_STATE_JSON)
        self.assertEqual(proc.stdout, b"")


class TestCliContract(TempDirCase):
    def test_sealed_tuples(self):
        self.assertEqual(batch_card.KNOWN_FLAGS,
                         ("--mode", "--head-blobs", "--subset", "--rows",
                          "--answer"))
        self.assertEqual(batch_card.SUBCOMMANDS,
                         ("rows", "select-questions", "select", "payload",
                          "parse", "decisions-report"))

    def test_select_questions_cli(self):
        path = self.write("rows.json", synth_rows(5))
        proc = run_cli(["select-questions", "--rows", path])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout),
                         batch_card.select_questions(synth_rows(5)["rows"]))

    def test_answer_side_usage_errors(self):
        rows = self.write("rows.json", synth_rows(3))
        ans = self.write("ans.json", {"all": True})
        for argv in (["select"], ["select", "--rows", rows],
                     ["select-questions", "--rows", rows, "--answer", ans],
                     ["parse", "--answer", ans],
                     ["payload", "--rows", rows],
                     ["select", "--rows", rows, "--answer", ans,
                      "--reason", "x"],
                     ["decisions-report", "--rows", rows]):
            with self.subTest(argv=argv):
                proc = run_cli(argv)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(proc.stderr.decode(), batch_card.USAGE)


# --------------------------------------------------------------------------- #
# Re-hash successor linkage (annotation only).
# --------------------------------------------------------------------------- #
SF = "app/a.py"
TITLE = "T"


def site(h, band="medium", status="persisted", at_pass=1, canonical="x = 1",
         file=SF, title=TITLE, line=11):
    """A finding whose snapshot matches its own fields (score.py's shape)."""
    snapshot = {"at_pass": at_pass, "file": file, "line": line,
                "canonical_line_content": canonical, "band": band}
    return mk_finding(band, status, h, file=file, line=line, title=title,
                      canonical_line_content=canonical, snapshot=snapshot)


def decision_for(finding, at_pass, reason="False positive",
                 decision="dismiss"):
    return {"decision": decision, "reason": reason, "at_pass": at_pass,
            "band": finding["band"],
            "evidence": carry_state._evidence_of(finding)}


def successor_state(band="medium"):
    """Pass 1: HA decided. Pass 2: the decided line was edited -> HB."""
    old = site(HA, band=band)
    s1 = mk_state([mk_pass(1, [old])])
    decided = dismiss(s1, HA, at_pass=1, reason="False positive")
    new = site(HB, band=band, status="new", at_pass=2, canonical="x = 2")
    out = copy.deepcopy(decided)
    out["passes"] = [mk_pass(1, [old]), mk_pass(2, [new])]
    return out


SUCCESSOR_TAG = {"cause": "code", "decision": "dismiss",
                 "reason": "False positive", "at_pass": 1,
                 "was_band": "medium", "via": "successor", "prior_hash": HA}


def stale_of(rows, h):
    return [r for r in rows if r["stable_hash"] == h][0]["stale"]


class TestSuccessor(unittest.TestCase):
    def test_successor_tagged(self):
        s = successor_state()
        self.assertNotEqual(HA, HB)
        self.assertNotIn(HA, [r["stable_hash"]
                              for r in carry_state.open_findings(s)])
        self.assertEqual(stale_of(rows_of(s), HB), SUCCESSOR_TAG)
        self.assertEqual(stale_of(rows_of(s, "finalize", {}), HB),
                         SUCCESSOR_TAG)

    def test_successor_tagged_through_cli(self):
        proc = run_cli(["rows", "--mode", "fix-loop"],
                       json.dumps(successor_state()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout)["rows"][0]["stale"],
                         SUCCESSOR_TAG)

    def test_successor_stays_open_and_counted(self):
        for band, key in (("medium", "unacknowledged_medium_hashes"),
                          ("critical", "outstanding_cw_hashes")):
            with self.subTest(band=band):
                s = successor_state(band)
                bare = copy.deepcopy(s)
                del bare["decisions"][HA]
                counts = carry_state.finalize_counts(s, {})
                self.assertIn(HB, counts[key])
                self.assertEqual(counts, carry_state.finalize_counts(bare, {}))
                verdicts = []
                for state in (s, bare):
                    proc = subprocess.run(
                        [sys.executable, os.path.join(HERE, "carry_state.py"),
                         "finalize-counts"], input=json.dumps(state).encode(),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        timeout=30)
                    self.assertEqual(proc.returncode, 0)
                    cli_counts = json.loads(proc.stdout)
                    verdicts.append(finalize_gate.decide({
                        "state_file_present": True, "noninteractive": False,
                        "pr_mode": False, "range_mode": False,
                        "outstanding_cw": cli_counts["outstanding_cw"],
                        "unacknowledged_medium":
                            cli_counts["unacknowledged_medium"]}))
                self.assertEqual(verdicts[0], verdicts[1])
                tagged = rows_of(s, "finalize", {})
                self.assertEqual([r["stable_hash"] for r in tagged], [HB])
                self.assertEqual([r["stable_hash"] for r in tagged],
                                 [r["stable_hash"]
                                  for r in rows_of(bare, "finalize", {})])

    def test_successor_ambiguous_no_annotation(self):
        s = successor_state()
        s["passes"][-1]["findings"].append(
            site(HC, status="new", at_pass=2, canonical="x = 3"))
        rows = rows_of(s)
        self.assertEqual(sorted(r["stable_hash"] for r in rows), [HB, HC])
        self.assertIsNone(stale_of(rows, HB))
        self.assertIsNone(stale_of(rows, HC))

    def _two_orphans(self, at_a, at_d):
        a = site(HA)
        d = site(HD, at_pass=2, canonical="x = 2")
        b = site(HB, status="new", at_pass=3, canonical="x = 3")
        return mk_state([mk_pass(1, [a]), mk_pass(2, [d]), mk_pass(3, [b])],
                        decisions={HA: decision_for(a, at_a, reason="old"),
                                   HD: decision_for(d, at_d, reason="new")})

    def test_successor_tie_break(self):
        stale = stale_of(rows_of(self._two_orphans(1, 2)), HB)
        self.assertEqual((stale["prior_hash"], stale["at_pass"],
                          stale["reason"]), (HD, 2, "new"))
        stale = stale_of(rows_of(self._two_orphans(2, 1)), HB)
        self.assertEqual(stale["prior_hash"], HA)
        stale = stale_of(rows_of(self._two_orphans(2, 2)), HB)
        self.assertEqual(stale["prior_hash"], HA)  # HA < HD

    def test_successor_requires_undecided_row(self):
        with self.subTest("own stale decision wins"):
            s = successor_state()
            b = s["passes"][-1]["findings"][0]
            s["decisions"][HB] = dict(decision_for(b, 2, reason="mine"),
                                      evidence=dict(
                                          carry_state._evidence_of(b),
                                          band="warning"))
            stale = stale_of(rows_of(s), HB)
            self.assertEqual((stale["via"], stale["prior_hash"],
                              stale["reason"]), ("same_hash", HB, "mine"))
        with self.subTest("own current decision: no tag"):
            s = successor_state()
            b = s["passes"][-1]["findings"][0]
            s["decisions"][HB] = decision_for(b, 2, reason="mine")
            self.assertNotIn(HB, [r["stable_hash"] for r in rows_of(s)])
            self.assertIsNone(stale_of(rows_of(s, subset=[HB]), HB))
        with self.subTest("legacy acknowledgment: no tag"):
            s = successor_state()
            s["medium_acknowledgments"][HB] = {"reason": "ack"}
            self.assertIsNone(stale_of(rows_of(s, subset=[HB]), HB))

    def test_successor_not_for_live_decision(self):
        a = site(HA, at_pass=2)
        b = site(HB, status="new", at_pass=2, canonical="x = 2")
        s = mk_state([mk_pass(1, [a]), mk_pass(2, [a, b])],
                     decisions={HA: decision_for(a, 1)})
        rows = rows_of(s)
        self.assertEqual([r["stable_hash"] for r in rows], [HB])
        self.assertIsNone(stale_of(rows, HB))

    def test_successor_from_member_obligation(self):
        member = member_ref(file=SF, line=11, title=TITLE)
        member["obligation"] = {"stable_hash": HA, "band": "medium",
                                "snapshot": snap(1, file=SF, line=11,
                                                 band="medium")}
        lead = mk_finding("warning", "persisted", HC, file="lib/other.py",
                          line=3, title="L", members=[member])
        b = site(HB, status="new", at_pass=2, canonical="x = 2")
        s = mk_state([mk_pass(1, [lead]), mk_pass(2, [b])],
                     decisions={HA: {"decision": "defer", "reason": "later",
                                     "at_pass": 1, "band": "medium",
                                     "evidence": {"file": SF, "line": 11,
                                                  "canonical_line_content":
                                                      "x = 1",
                                                  "band": "medium"}}})
        stale = stale_of(rows_of(s), HB)
        self.assertEqual(stale, {"cause": "code", "decision": "defer",
                                 "reason": "later", "at_pass": 1,
                                 "was_band": "medium", "via": "successor",
                                 "prior_hash": HA})

    def test_successor_without_earlier_identity_or_evidence(self):
        with self.subTest("no earlier identity"):
            s = successor_state()
            s["passes"] = s["passes"][1:]
            self.assertIsNone(stale_of(rows_of(s), HB))
        with self.subTest("pre-47 decision: was_band from the record"):
            s = successor_state()
            del s["decisions"][HA]["evidence"]
            s["decisions"][HA]["band"] = "warning"
            self.assertEqual(stale_of(rows_of(s), HB)["was_band"], "warning")

    def test_successor_different_title_or_file(self):
        for field, value in (("title", "T2"), ("file", "app/b.py")):
            with self.subTest(field=field):
                s = successor_state()
                s["passes"][-1]["findings"][0][field] = value
                self.assertIsNone(stale_of(rows_of(s), HB))

    def test_successor_mutation(self):
        s = successor_state()
        with self.subTest("real"):
            self.assertEqual(stale_of(rows_of(s), HB), SUCCESSOR_TAG)
        with self.subTest("mutant"):
            with mock.patch.object(batch_card, "successor_links",
                                   return_value={}):
                tag = stale_of(rows_of(s), HB)
            self.assertIsNone(tag)
            with self.assertRaises(AssertionError):
                self.assertEqual(tag, SUCCESSOR_TAG)


if __name__ == "__main__":
    unittest.main()
