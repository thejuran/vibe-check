"""test_bottom_line_suggest.py — what the Bottom line may suggest (D-19).

The report's Bottom line offers the owner a ready-made answer. It is written
by the model from diff-influenced report text, so `batch_card.py suggest`
trims it before the owner sees it: `fix` may name any row, but `dismiss` and
`defer` may name MEDIUM rows only. A suggested dismiss/defer of a critical,
warning or needs-verification row is dropped, so typing "bottom line" can
never dismiss or defer a serious row; those still need the owner's own words.

The parser stays the only gate: the suggestion is parsed before trimming and
the trimmed grammar is parsed again, so the helper never emits a grammar the
gate would refuse. `rest` and `all` are expanded to explicit numbers, so the
card prints exactly what will be applied. Refusals and the trimmed notice are
fixed lines with no owner text.
"""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module under test)
import batch_parse  # noqa: E402
import carry_state  # noqa: E402
from test_batch_card import ALL_REASONS, TempDirCase, run_cli  # noqa: E402
from test_answer_resolve import _rebanded, iplayarr_rows  # noqa: E402

# iplayarr_rows: rows 1-3 critical, 4-7 warning, 8 medium.
MEDIUM_ROW = 8
NV_ROW = 6
TRIMMED_LINE = ("suggestion trimmed: %d serious row(s) dropped — dismiss or "
                "defer those in your own words\n")
OWNER_WORDS = ("false positive", "noise", "later", "Browse", "zebra")


def answer(q1, q2=None):
    return {"q1": q1, "q2": q2}


def suggest_ok(rows_doc, ans):
    out, reason = batch_card.suggest(rows_doc, ans)
    assert reason is None, reason
    return out


def acted_on(rows_doc, ans):
    """{verb: sorted row numbers} the unchanged parser acts on for `ans`."""
    parsed, reason = batch_card.parse(rows_doc, ans)
    assert reason is None, reason
    n_of = {r["stable_hash"]: r["n"] for r in rows_doc["rows"]}
    return {verb: sorted(n_of[h] for h in parsed[verb])
            for verb in batch_parse.VERBS}


# Lock checks shared by the real tests and the mutants. Each raises
# AssertionError when the guarded behavior is broken.
def check_dismiss_critical_dropped(tc):
    out, dropped = suggest_ok(
        iplayarr_rows(), answer("fix 5; dismiss 1,2 -- false positive"))
    tc.assertEqual(out, {"q1": "fix 5", "q2": None})
    tc.assertEqual(dropped, [1, 2])


def check_all_dropped_refuses(tc):
    out, reason = batch_card.suggest(iplayarr_rows(),
                                     answer("dismiss 1,2,3 -- fp"))
    tc.assertIsNone(out)
    tc.assertEqual(reason, batch_card.REASON_SUGGEST_EMPTY)


def check_output_passes_parse(tc, rows_doc, ans):
    """The emitted object parses as is and acts on the same rows."""
    result, reason = batch_card.suggest(rows_doc, ans)
    if reason is not None:
        return
    out, _ = result
    tc.assertEqual(set(out), {"q1", "q2"})
    parsed, parse_reason = batch_card.parse(rows_doc, out)
    tc.assertIsNone(parse_reason, "suggest emitted a grammar parse refuses")
    tc.assertIsNotNone(parsed)


class TestSuggest(unittest.TestCase):
    def test_fixture_bands(self):
        bands = [r["band"] for r in iplayarr_rows()["rows"]]
        self.assertEqual(bands, ["critical"] * 3 + ["warning"] * 4
                         + ["medium"])

    def test_fix_any_band_kept(self):
        out, dropped = suggest_ok(iplayarr_rows(), answer("fix 1,2,5"))
        self.assertEqual(out, {"q1": "fix 1,2,5", "q2": None})
        self.assertEqual(dropped, [])

    def test_dismiss_critical_dropped(self):
        check_dismiss_critical_dropped(self)

    def test_defer_warning_dropped(self):
        out, dropped = suggest_ok(
            iplayarr_rows(), answer("fix 1; defer 4,8 -- later"))
        self.assertEqual(out, {"q1": "fix 1; defer 8 -- later", "q2": None})
        self.assertEqual(dropped, [4])

    def test_dismiss_medium_kept(self):
        out, dropped = suggest_ok(
            iplayarr_rows(), answer("fix 5; dismiss %d -- noise" % MEDIUM_ROW))
        self.assertEqual(out, {"q1": "fix 5; dismiss %d -- noise" % MEDIUM_ROW,
                               "q2": None})
        self.assertEqual(dropped, [])

    def test_rest_expanded_to_numbers(self):
        out, dropped = suggest_ok(iplayarr_rows(),
                                  answer("fix 1; defer rest -- later"))
        self.assertEqual(out, {"q1": "fix 1; defer %d -- later" % MEDIUM_ROW,
                               "q2": None})
        self.assertNotIn("rest", out["q1"])
        self.assertEqual(dropped, [])

    def test_fix_rest_expanded_to_numbers(self):
        out, _ = suggest_ok(iplayarr_rows(), answer("fix rest"))
        self.assertEqual(out["q1"], "fix 1,2,3,4,5,6,7,8")

    def test_q2_reason_folded_into_grammar(self):
        out, _ = suggest_ok(iplayarr_rows(),
                            answer("dismiss %d" % MEDIUM_ROW, "noise"))
        self.assertEqual(out, {"q1": "dismiss %d -- noise" % MEDIUM_ROW,
                               "q2": None})

    def test_nv_row_dropped(self):
        rows_doc = _rebanded(iplayarr_rows(), NV_ROW, carry_state.NV_BAND)
        out, reason = batch_card.suggest(rows_doc,
                                         answer("defer %d -- later" % NV_ROW))
        self.assertIsNone(out)
        self.assertEqual(reason, batch_card.REASON_SUGGEST_EMPTY)

    def test_nv_row_fix_kept(self):
        rows_doc = _rebanded(iplayarr_rows(), NV_ROW, carry_state.NV_BAND)
        out, dropped = suggest_ok(rows_doc, answer("fix %d" % NV_ROW))
        self.assertEqual(out["q1"], "fix %d" % NV_ROW)
        self.assertEqual(dropped, [])

    def test_all_dropped_refuses(self):
        check_all_dropped_refuses(self)

    def test_look_only_refuses_empty(self):
        out, reason = batch_card.suggest(iplayarr_rows(), answer("look 3"))
        self.assertIsNone(out)
        self.assertEqual(reason, batch_card.REASON_SUGGEST_EMPTY)

    def test_output_passes_parse_unchanged(self):
        expectations = {
            "fix 1,2,5": {"fix": [1, 2, 5], "dismiss": [], "defer": []},
            "fix 5; dismiss 1,2 -- false positive":
                {"fix": [5], "dismiss": [], "defer": []},
            "fix 5; dismiss 8 -- noise":
                {"fix": [5], "dismiss": [8], "defer": []},
            "fix 1; defer rest -- later":
                {"fix": [1], "dismiss": [], "defer": [8]},
            "fix 1; defer 4,8 -- later":
                {"fix": [1], "dismiss": [], "defer": [8]},
        }
        rows_doc = iplayarr_rows()
        for q1, want in expectations.items():
            with self.subTest(q1=q1):
                out, _ = suggest_ok(rows_doc, answer(q1))
                check_output_passes_parse(self, rows_doc, answer(q1))
                self.assertEqual(acted_on(rows_doc, out), want)

    def test_parser_refusals_pass_through(self):
        rows_doc = iplayarr_rows()
        cases = (
            (answer("nonsense"), batch_parse.REASON_TOKEN),
            (answer("dismiss 8"), batch_parse.REASON_NO_REASON),
            (answer("fix 99"), batch_parse.REASON_RANGE),
            ({"q1": 3}, batch_card.REASON_ANSWER),
            ({"q1": "fix 1", "q3": "x"}, batch_card.REASON_ANSWER),
            ("fix 1", batch_card.REASON_ANSWER),
        )
        for ans, want in cases:
            with self.subTest(ans=ans):
                self.assertEqual(batch_card.suggest(rows_doc, ans),
                                 (None, want))

    def test_suggest_reason_is_registered(self):
        self.assertIn(batch_card.REASON_SUGGEST_EMPTY, batch_card.REASONS)
        self.assertNotIn("suggest", batch_card._STATE_SUBCOMMANDS)
        self.assertEqual(batch_card._FLAGS_BY_SUBCOMMAND["suggest"],
                         (("--rows", "--answer"), ()))
        self.assertIn("suggest --rows PATH --answer PATH", batch_card.USAGE)


class TestSuggestCli(TempDirCase):
    def _run(self, ans, rows_doc=None, stdin_bytes=b""):
        rows_doc = iplayarr_rows() if rows_doc is None else rows_doc
        argv = ["suggest", "--rows", self.write("rows.json", rows_doc),
                "--answer", self.write("ans.json", ans)]
        return run_cli(argv, stdin_bytes=stdin_bytes)

    def test_prints_trimmed_object(self):
        proc = self._run(answer("fix 5; dismiss 1,2 -- false positive"))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout), {"q1": "fix 5", "q2": None})
        self.assertEqual(proc.stderr.decode(), TRIMMED_LINE % 2)

    def test_untrimmed_has_quiet_stderr(self):
        proc = self._run(answer("fix 5; dismiss 8 -- noise"))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout),
                         {"q1": "fix 5; dismiss 8 -- noise", "q2": None})
        self.assertEqual(proc.stderr, b"")

    def test_output_file_is_a_valid_parse_answer(self):
        proc = self._run(answer("fix 1; defer rest -- later"))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        path = self.write("suggest.json", proc.stdout.decode())
        parsed = run_cli(["parse", "--rows",
                          self.write("rows2.json", iplayarr_rows()),
                          "--answer", path])
        self.assertEqual(parsed.returncode, 0, parsed.stderr.decode())

    def test_refusals_are_fixed_reasons_without_owner_text(self):
        reasons = set(ALL_REASONS) | {batch_card.REASON_SUGGEST_EMPTY}
        cases = {
            "all dropped": answer("dismiss 1,2,3 -- false positive"),
            "grammar": answer("zebra Browse"),
            "no reason": answer("dismiss 8"),
            "malformed": {"q1": ["noise"]},
            "not json": "later zebra",
        }
        for name, ans in cases.items():
            with self.subTest(name):
                proc = self._run(ans)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                err = proc.stderr.decode()
                self.assertIn(err, reasons)
                for word in OWNER_WORDS:
                    self.assertNotIn(word, err)

    def test_all_dropped_exit_2_with_empty_reason(self):
        proc = self._run(answer("dismiss 1,2,3 -- fp"))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stderr.decode(),
                         batch_card.REASON_SUGGEST_EMPTY)

    def test_usage_refusals(self):
        rows = self.write("rows.json", iplayarr_rows())
        ans = self.write("ans.json", answer("fix 1"))
        for argv in (["suggest"], ["suggest", "--rows", rows],
                     ["suggest", "--answer", ans],
                     ["suggest", "--rows", rows, "--answer", ans,
                      "--prior-rows", rows],
                     ["suggest", "--rows", rows, "--answer", ans,
                      "--mode", "fix-loop"]):
            with self.subTest(argv=argv[1:]):
                proc = run_cli(argv)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertEqual(proc.stderr.decode(), batch_card.USAGE)

    def test_reads_no_stdin(self):
        proc = self._run(answer("fix 1,2,5"), stdin_bytes=b"garbage \xff")
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout),
                         {"q1": "fix 1,2,5", "q2": None})


if __name__ == "__main__":
    unittest.main()
