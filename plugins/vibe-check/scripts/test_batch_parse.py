"""test_batch_parse.py — the batch-card answer grammar as executable decisions.

`batch_parse.py` turns the owner's answer to a batch card into per-row verbs:

* `parse_answer(rows, q1, q2)` reads the finalize card. Q1 is one of the four
  buttons (Dismiss all / Defer all / Fix all / Mixed…) or typed text in the
  Mixed… grammar (`fix 2,5; defer 3; dismiss rest`, or `look N` alone). Q2 is
  the one reason covering every dismissed and deferred row.
* `parse_selection(rows, labels=..., text=...)` maps a multi-select answer or a
  typed list (`1,3-5`) back to row numbers by the leading `#n` token only.

Safety rule: a bulk form (`dismiss rest`, `defer rest`, and the Dismiss all /
Defer all buttons) only ever reaches MEDIUM rows. A critical or warning row is
dismissed or deferred only when the owner names it by number. Every refusal is
a fixed string from REASONS that never echoes owner text.
"""

import ast
import os
import unittest
from unittest import mock

import batch_parse
from batch_parse import (
    FINALIZE_Q1,
    FINALIZE_Q2,
    FIX_LOOP_OPTIONS,
    REASONS,
    REASON_DUPLICATE,
    REASON_EMPTY,
    REASON_LABEL,
    REASON_LOOK_MIXED,
    REASON_NO_REASON,
    REASON_RANGE,
    REASON_REST_TWICE,
    REASON_TOKEN,
    STOP_OPTIONS,
    parse_answer,
    parse_selection,
)

BATCH_PARSE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "batch_parse.py")

BANDS = ("critical", "warning", "medium", "medium", "medium")
FILES = ("app/a.py", "app/b.py", "app/c.py", "app/d.py", "app/e.py")
LINES = (3, 7, 11, None, 1)


def make_rows():
    return [
        {"n": i + 1, "stable_hash": str(i + 1) * 64, "band": BANDS[i],
         "file": FILES[i], "line": LINES[i], "title": "t%d, with comma" % (i + 1)}
        for i in range(5)
    ]


def h(*ns):
    return [str(n) * 64 for n in ns]


UNDECIDED_CW_DISMISS = ("2 critical/warning not covered by 'dismiss rest'"
                        " — still open; finalize stays blocked")


class TestLabels(unittest.TestCase):
    def test_card_labels_are_sealed(self):
        self.assertEqual(FIX_LOOP_OPTIONS, ("Apply all & rerun", "Apply selected…",
                                            "Skip & rerun", "Stop here…"))
        self.assertEqual(STOP_OPTIONS, ("Close out", "Abandon",
                                        "I'll fix by hand, then rerun"))
        self.assertEqual(FINALIZE_Q1, ("Dismiss all", "Defer all", "Fix all",
                                       "Mixed…"))
        self.assertEqual(FINALIZE_Q2, ("False positive", "Accepted risk",
                                       "Out of scope for this milestone"))


class TestReasons(unittest.TestCase):
    def test_reasons_tuple_is_complete_and_newline_terminated(self):
        expected = {REASON_EMPTY, REASON_TOKEN, REASON_RANGE, REASON_DUPLICATE,
                    REASON_REST_TWICE, REASON_LOOK_MIXED, REASON_NO_REASON,
                    REASON_LABEL}
        self.assertEqual(set(REASONS), expected)
        self.assertEqual(len(REASONS), 8)
        for reason in REASONS:
            self.assertTrue(reason.endswith("\n"), reason)

    def test_refusals_never_echo_owner_text(self):
        rows = make_rows()
        bad_q1 = ("ZZMARKER", "fix ZZMARKER", "fix 99 ZZMARKER", "look 1; ZZMARKER",
                  "dismiss 3")
        for q1 in bad_q1:
            with self.subTest(q1=q1):
                out = parse_answer(rows, q1, "ZZMARKER" if q1 != "dismiss 3" else "")
                self.assertIsInstance(out, tuple)
                self.assertIsNone(out[0])
                self.assertIn(out[1], REASONS)
                self.assertNotIn("ZZMARKER", out[1])
        for reason in REASONS:
            self.assertNotIn("ZZMARKER", reason)


class TestButtons(unittest.TestCase):
    def test_fix_all_takes_every_band(self):
        out = parse_answer(make_rows(), "Fix all", None)
        self.assertTrue(out["ok"])
        self.assertFalse(out["need_text"])
        self.assertIsNone(out["look"])
        self.assertEqual(out["fix"], h(1, 2, 3, 4, 5))
        self.assertEqual(out["dismiss"], [])
        self.assertEqual(out["defer"], [])
        self.assertEqual(out["undecided"], [])
        self.assertIsNone(out["reason"])
        fix_lines = [line for line in out["echo"] if line.startswith("fix")]
        self.assertEqual(len(fix_lines), 1)
        for n in range(1, 6):
            self.assertIn("#%d " % n, fix_lines[0])

    def test_fix_all_ignores_q2(self):
        out = parse_answer(make_rows(), "Fix all", "False positive")
        self.assertIsNone(out["reason"])

    def test_dismiss_all_reaches_mediums_only(self):
        out = parse_answer(make_rows(), "Dismiss all", "False positive")
        self.assertTrue(out["ok"])
        self.assertEqual(out["dismiss"], h(3, 4, 5))
        self.assertEqual(out["undecided"], h(1, 2))
        self.assertEqual(out["fix"], [])
        self.assertEqual(out["defer"], [])
        self.assertIn(UNDECIDED_CW_DISMISS, out["echo"])
        self.assertEqual(out["reason"], "False positive")

    def test_defer_all_reaches_mediums_only(self):
        out = parse_answer(make_rows(), "Defer all", "Accepted risk")
        self.assertEqual(out["defer"], h(3, 4, 5))
        self.assertEqual(out["undecided"], h(1, 2))
        self.assertEqual(out["dismiss"], [])
        self.assertEqual(out["reason"], "Accepted risk")
        self.assertIn("2 critical/warning not covered by 'defer rest'"
                      " — still open; finalize stays blocked", out["echo"])

    def test_bare_mixed_needs_text(self):
        for q2 in (None, "False positive"):
            with self.subTest(q2=q2):
                out = parse_answer(make_rows(), "Mixed…", q2)
                self.assertTrue(out["ok"])
                self.assertTrue(out["need_text"])
                self.assertIsNone(out["look"])
                for key in ("fix", "dismiss", "defer", "undecided", "echo"):
                    self.assertEqual(out[key], [], key)

    def test_q2_labels_returned_verbatim(self):
        for label in FINALIZE_Q2:
            with self.subTest(label=label):
                out = parse_answer(make_rows(), "Dismiss all", label)
                self.assertEqual(out["reason"], label)

    def test_typed_reason_is_stripped(self):
        out = parse_answer(make_rows(), "Dismiss all", "  my reason  ")
        self.assertEqual(out["reason"], "my reason")


class TestMixedGrammar(unittest.TestCase):
    def test_success_table(self):
        table = [
            ("fix 2,5; defer 3; dismiss rest", "Out of scope for this milestone",
             {"fix": h(2, 5), "defer": h(3), "dismiss": h(4), "undecided": h(1)}),
            ("dismiss 1", "typed reason",
             {"fix": [], "defer": [], "dismiss": h(1), "undecided": h(2, 3, 4, 5)}),
            ("FIX 1-3 ;  dismiss rest ;", "r",
             {"fix": h(1, 2, 3), "defer": [], "dismiss": h(4, 5), "undecided": []}),
            ("defer 2; fix rest", "r",
             {"fix": h(1, 3, 4, 5), "defer": h(2), "dismiss": [], "undecided": []}),
            ("fix 3", None,
             {"fix": h(3), "defer": [], "dismiss": [], "undecided": h(1, 2, 4, 5)}),
            ("  fix 1 , 2 ;dismiss 3-5", "r",
             {"fix": h(1, 2), "defer": [], "dismiss": h(3, 4, 5), "undecided": []}),
        ]
        for q1, q2, want in table:
            with self.subTest(q1=q1):
                out = parse_answer(make_rows(), q1, q2)
                self.assertIsInstance(out, dict, out)
                self.assertTrue(out["ok"])
                self.assertFalse(out["need_text"])
                self.assertIsNone(out["look"])
                for key, val in want.items():
                    self.assertEqual(out[key], val, key)

    def test_named_cw_may_be_dismissed(self):
        out = parse_answer(make_rows(), "dismiss 1, 2", "r")
        self.assertEqual(out["dismiss"], h(1, 2))
        self.assertEqual(out["undecided"], h(3, 4, 5))

    def test_look_alone(self):
        out = parse_answer(make_rows(), "look 3", None)
        self.assertTrue(out["ok"])
        self.assertFalse(out["need_text"])
        self.assertEqual(out["look"], 3)
        for key in ("fix", "dismiss", "defer", "undecided"):
            self.assertEqual(out[key], [], key)
        self.assertIsNone(out["reason"])

    def test_refusal_table(self):
        table = [
            ("", None, REASON_EMPTY),
            ("   ", None, REASON_EMPTY),
            (" ; ", None, REASON_EMPTY),
            (None, None, REASON_EMPTY),
            ("fix 9", None, REASON_RANGE),
            ("fix 3-2", None, REASON_RANGE),
            ("fix 0", None, REASON_RANGE),
            ("fix 1-9", None, REASON_RANGE),
            ("look 6", None, REASON_RANGE),
            ("look 0", None, REASON_RANGE),
            ("fix 2; dismiss 2", "r", REASON_DUPLICATE),
            ("fix 1-3; defer 3", "r", REASON_DUPLICATE),
            ("fix 2,2", None, REASON_DUPLICATE),
            ("dismiss rest; defer rest", "r", REASON_REST_TWICE),
            ("fix rest; fix rest", None, REASON_REST_TWICE),
            ("look 2; fix 1", None, REASON_LOOK_MIXED),
            ("look 1; look 2", None, REASON_LOOK_MIXED),
            ("delete 2", None, REASON_TOKEN),
            ("fix two", None, REASON_TOKEN),
            ("fix 1 2", None, REASON_TOKEN),
            ("fix all", None, REASON_TOKEN),
            ("fix", None, REASON_TOKEN),
            ("fix 1,", None, REASON_TOKEN),
            ("fix 1;; dismiss 2", "r", REASON_TOKEN),
            ("fix -1", None, REASON_TOKEN),
            ("look", None, REASON_TOKEN),
            ("look 1-2", None, REASON_TOKEN),
            ("Mixed… fix 1", None, REASON_TOKEN),
            ("dismiss 3", "", REASON_NO_REASON),
            ("dismiss 3", None, REASON_NO_REASON),
            ("defer 3", "   ", REASON_NO_REASON),
            ("Dismiss all", None, REASON_NO_REASON),
        ]
        for q1, q2, reason in table:
            with self.subTest(q1=q1, q2=q2):
                self.assertEqual(parse_answer(make_rows(), q1, q2), (None, reason))


class TestEcho(unittest.TestCase):
    def test_echo_order_and_rows(self):
        out = parse_answer(make_rows(), "defer 3; dismiss 4; fix 2,5", "r")
        verbs = [line.split(":", 1)[0] for line in out["echo"][:3]]
        self.assertEqual(verbs, ["fix", "dismiss", "defer"])
        self.assertIn("#2 app/b.py:7", out["echo"][0])
        self.assertIn("#5 app/e.py:1", out["echo"][0])
        self.assertIn("#4 app/d.py", out["echo"][1])
        self.assertNotIn("app/d.py:", out["echo"][1])
        self.assertIn("#3 app/c.py:11", out["echo"][2])

    def test_echo_lists_still_open_rows(self):
        out = parse_answer(make_rows(), "dismiss 1", "r")
        joined = "\n".join(out["echo"])
        for n in (2, 3, 4, 5):
            self.assertIn("#%d " % n, joined)
        self.assertIn("still open", joined)

    def test_echo_never_carries_titles_or_owner_text(self):
        out = parse_answer(make_rows(), "fix 2,5; defer 3; dismiss rest",
                           "ZZREASON")
        joined = "\n".join(out["echo"])
        self.assertNotIn("fix 2,5", joined)
        self.assertNotIn("ZZREASON", joined)
        self.assertNotIn("with comma", joined)


class TestSelection(unittest.TestCase):
    def test_labels_map_by_leading_number(self):
        out = parse_selection(make_rows(), labels=["#2 app/b.py:7", "#5 app/e.py:1"])
        self.assertEqual(out, {"ok": True, "rows": [2, 5], "hashes": h(2, 5)})

    def test_joined_label_string(self):
        out = parse_selection(make_rows(), labels="#5 app/e.py:1, #2 app/b.py:7")
        self.assertEqual(out["rows"], [2, 5])
        self.assertEqual(out["hashes"], h(2, 5))

    def test_label_number_wins_over_text(self):
        # The text after the number is never consulted.
        out = parse_selection(make_rows(), labels=["#1 app/e.py:1"])
        self.assertEqual(out["rows"], [1])

    def test_typed_lists(self):
        table = [
            ("1,3-5", [1, 3, 4, 5]),
            ("5,1", [1, 5]),
            (" 2 , 4 ", [2, 4]),
        ]
        for text, rows in table:
            with self.subTest(text=text):
                out = parse_selection(make_rows(), text=text)
                self.assertEqual(out["rows"], rows)
                self.assertEqual(out["hashes"], h(*rows))

    def test_selection_refusals(self):
        table = [
            ({"labels": ["app/b.py:7"]}, REASON_LABEL),
            ({"labels": ["#x app/b.py:7"]}, REASON_LABEL),
            ({"labels": ["#2app/b.py:7"]}, REASON_LABEL),
            ({"labels": ["Apply all & rerun"]}, REASON_LABEL),
            ({"labels": ["#9 app/z.py:1"]}, REASON_RANGE),
            ({"labels": ["#2 a", "#2 b"]}, REASON_DUPLICATE),
            ({"labels": []}, REASON_EMPTY),
            ({"text": ""}, REASON_EMPTY),
            ({"text": "  "}, REASON_EMPTY),
            ({"text": "1,9"}, REASON_RANGE),
            ({"text": "0"}, REASON_RANGE),
            ({"text": "4-2"}, REASON_RANGE),
            ({"text": "1,1"}, REASON_DUPLICATE),
            ({"text": "1-3,2"}, REASON_DUPLICATE),
            ({"text": "1;2"}, REASON_TOKEN),
            ({"text": "1 2"}, REASON_TOKEN),
            ({"text": "one"}, REASON_TOKEN),
            ({}, REASON_EMPTY),
            ({"labels": None, "text": None}, REASON_EMPTY),
        ]
        for kwargs, reason in table:
            with self.subTest(kwargs=kwargs):
                self.assertEqual(parse_selection(make_rows(), **kwargs),
                                 (None, reason))


class TestRowsValidation(unittest.TestCase):
    def test_malformed_rows_raise(self):
        good = make_rows()
        bad_variants = []
        gap = make_rows()
        gap[2]["n"] = 4
        bad_variants.append(gap)
        zero = make_rows()
        for row in zero:
            row["n"] -= 1
        bad_variants.append(zero)
        no_hash = make_rows()
        del no_hash[0]["stable_hash"]
        bad_variants.append(no_hash)
        bad_band = make_rows()
        bad_band[0]["band"] = "low"
        bad_variants.append(bad_band)
        bool_n = make_rows()[:1]
        bool_n[0]["n"] = True
        bad_variants.append(bool_n)
        bad_variants.append("not a list")
        for rows in bad_variants:
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    parse_answer(rows, "Fix all", None)
                with self.assertRaises(ValueError):
                    parse_selection(rows, text="1")
        self.assertTrue(parse_answer(good, "Fix all", None)["ok"])


class TestMutants(unittest.TestCase):
    """Contrast subtests: each guard is load-bearing."""

    def test_m1_rest_band_filter_is_load_bearing(self):
        real = parse_answer(make_rows(), "Dismiss all", "r")
        self.assertNotIn(h(1)[0], real["dismiss"])
        self.assertIn(h(1)[0], real["undecided"])
        with mock.patch.object(batch_parse, "_rest_bands_for",
                               lambda verb: ("critical", "warning", "medium")):
            mutant = parse_answer(make_rows(), "Dismiss all", "r")
        self.assertIn(h(1)[0], mutant["dismiss"])
        self.assertNotIn(h(1)[0], mutant["undecided"])

    def test_m1_fix_rest_reaches_cw(self):
        self.assertEqual(batch_parse._rest_bands_for("fix"),
                         ("critical", "warning", "medium"))
        self.assertEqual(batch_parse._rest_bands_for("dismiss"), ("medium",))
        self.assertEqual(batch_parse._rest_bands_for("defer"), ("medium",))

    def test_m2_duplicate_check_is_load_bearing(self):
        self.assertEqual(parse_answer(make_rows(), "fix 2; dismiss 2", "r"),
                         (None, REASON_DUPLICATE))

        def overwrite(assigned, n, verb):
            assigned[n] = verb
            return True

        with mock.patch.object(batch_parse, "_assign", overwrite):
            mutant = parse_answer(make_rows(), "fix 2; dismiss 2", "r")
        self.assertIsInstance(mutant, dict)
        self.assertTrue(mutant["ok"])


class TestImportSet(unittest.TestCase):
    ALLOWED = {"re", "json"}

    def test_import_set_is_stdlib_and_never_carry_state(self):
        with open(BATCH_PARSE_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(imported <= self.ALLOWED, imported)
        self.assertNotIn("carry_state", imported)

    def test_no_file_or_process_calls(self):
        with open(BATCH_PARSE_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"open", "exec", "eval",
                                                "__import__"})


if __name__ == "__main__":
    unittest.main()
