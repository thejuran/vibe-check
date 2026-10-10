"""Tests for harness_cards: classify each card, answer it from the seeded
identity only, and classify the text a turn ends on.

Card text is rendered by the plugin's own `batch_card` helpers, so the row
parser is tested against the exact shape the plugin prints.

Run with bare `pytest -q` from this directory.
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_cards as hc  # noqa: E402

sys.path.insert(0, str(hc.PLUGIN_SCRIPTS_DIR))

import batch_card  # noqa: E402
import batch_parse  # noqa: E402

SEEDED = ("src/clamp.py", "clamp returns a value above the upper bound")
NOISE_A = ("src/util.py", "unused import of os")
NOISE_B = ("src/io.py", "file handle is never closed")


def _rows(*items):
    """Plugin-shaped rows: (file, title, band) in card order."""
    out = []
    for i, (file, title, band) in enumerate(items, start=1):
        out.append({"n": i, "file": file, "line": 10 * i, "title": title,
                    "band": band, "stable_hash": "%040x" % i,
                    "problem": "problem text for row %d" % i})
    return out


def _options(labels, descriptions=None):
    descriptions = descriptions or ["" for _ in labels]
    return [{"label": label, "description": desc}
            for label, desc in zip(labels, descriptions)]


def fix_loop_card(rows, pass_number=2):
    text = batch_card.card_texts(rows, "fix-loop")["card_text"]
    question = ("Pass %d — %d finding(s) listed below. How do you want to "
                "proceed?\n\n%s" % (pass_number, len(rows), text))
    return {"questions": [{
        "header": "Pass %d" % pass_number,
        "question": question,
        "multiSelect": False,
        "options": _options(batch_parse.FIX_LOOP_OPTIONS),
    }]}


def select_card(rows):
    shape = batch_card.select_questions(rows)
    assert shape["mode"] == "multiselect", shape["mode"]
    return {"questions": shape["questions"]}


def stop_card(pass_number=2):
    return {"questions": [{
        "header": "Stop here",
        "question": "Pass %d — how do you want to stop?" % pass_number,
        "multiSelect": False,
        "options": _options(batch_parse.STOP_OPTIONS),
    }]}


def finalize_card(rows, with_q2=True):
    text = batch_card.card_texts(rows, "finalize")["card_text"]
    q1 = {"header": "Decide",
          "question": ("Finalize — %d undecided finding(s) listed below. What "
                       "should happen to them?\n\n%s" % (len(rows), text)),
          "multiSelect": False,
          "options": _options(batch_parse.FINALIZE_Q1)}
    questions = [q1]
    if with_q2:
        questions.append({
            "header": "Reason",
            "question": ("One reason for everything dismissed or deferred "
                         "(ignored when nothing is dismissed or deferred). "
                         "Pick one, or type your own in Other."),
            "multiSelect": False,
            "options": _options(batch_parse.FINALIZE_Q2)})
    return {"questions": questions}


def first_run_card():
    return {"questions": [{
        "header": "Migrate",
        "question": ("Found old TuringMind state under `.gsd/`. Move to "
                     "`.turingmind/`?"),
        "multiSelect": False,
        "options": _options(["Yes, move it", "No, leave it",
                             "Delete the old state"]),
    }]}


def estimate_card():
    return {"questions": [{
        "header": "Estimate",
        "question": "About to review 40 files in 3 chunks. Proceed?",
        "multiSelect": False,
        "options": _options(["Run full", "Narrow scope",
                             "Cap at top-K chunks", "Cancel"]),
    }]}


def _q(card, i=0):
    return card["questions"][i]["question"]


class TestPluginLabelsMeanWhatTheHarnessAssumes(unittest.TestCase):
    """The harness indexes the plugin's tuples; pin what each index means so
    a reorder in the plugin cannot silently make the harness pick another
    option."""

    def test_indexed_labels(self):
        self.assertEqual(hc.APPLY_ALL, "Apply all & rerun")
        self.assertEqual(hc.APPLY_SELECTED, "Apply selected…")
        self.assertEqual(hc.CLOSE_OUT, "Close out")
        self.assertEqual(hc.FIX_ALL, "Fix all")
        self.assertEqual(hc.OUT_OF_SCOPE, "Out of scope for this milestone")

    def test_labels_are_the_plugin_objects(self):
        self.assertIs(hc.APPLY_ALL, batch_parse.FIX_LOOP_OPTIONS[0])
        self.assertIs(hc.CLOSE_OUT, batch_parse.STOP_OPTIONS[0])
        self.assertIs(hc.FIX_ALL, batch_parse.FINALIZE_Q1[2])
        self.assertIs(hc.OUT_OF_SCOPE, batch_parse.FINALIZE_Q2[2])


class TestClassifyCard(unittest.TestCase):

    def test_fix_loop(self):
        card = fix_loop_card(_rows(SEEDED + ("critical",)))
        self.assertEqual(hc.classify_card(card), hc.FIX_LOOP)

    def test_select(self):
        card = select_card(_rows(NOISE_A + ("warning",),
                                 SEEDED + ("critical",)))
        self.assertEqual(hc.classify_card(card), hc.FIX_LOOP_SELECT)

    def test_stop(self):
        self.assertEqual(hc.classify_card(stop_card()), hc.STOP)

    def test_finalize_with_and_without_q2(self):
        rows = _rows(SEEDED + ("critical",))
        self.assertEqual(hc.classify_card(finalize_card(rows)), hc.FINALIZE)
        self.assertEqual(hc.classify_card(finalize_card(rows, with_q2=False)),
                         hc.FINALIZE)

    def test_unknown_shapes(self):
        rows = _rows(SEEDED + ("critical",))
        bad_q2 = finalize_card(rows)
        bad_q2["questions"][1]["options"] = _options(["Because"])
        extra_label = fix_loop_card(rows)
        extra_label["questions"][0]["options"].append(
            {"label": "Do something else", "description": ""})
        not_multi = select_card(_rows(NOISE_A + ("warning",),
                                      SEEDED + ("critical",)))
        for q in not_multi["questions"]:
            q["multiSelect"] = False
        for card in (first_run_card(), estimate_card(), bad_q2, extra_label,
                     not_multi, {}, {"questions": []}, None, "text",
                     {"questions": [{"options": "x"}]}):
            with self.subTest(card=card):
                self.assertEqual(hc.classify_card(card), hc.UNKNOWN)


class TestParseRows(unittest.TestCase):

    def test_rows_from_plugin_rendering(self):
        rows = _rows(NOISE_A + ("warning",), SEEDED + ("critical",),
                     NOISE_B + ("medium",))
        rows[1]["pending_since"] = 1
        got = hc.parse_rows(_q(finalize_card(rows)))
        self.assertEqual(
            got,
            [hc.Row(1, NOISE_A[0], 10, NOISE_A[1], "warning"),
             hc.Row(2, SEEDED[0], 20, SEEDED[1], "critical"),
             hc.Row(3, NOISE_B[0], 30, NOISE_B[1], "medium")])

    def test_unknown_line_and_non_row_lines(self):
        text = ("Pass 1 — 1 finding(s)\n\n#1 src/a.py:? — a title (warning)\n"
                "    problem line\nnot a row")
        self.assertEqual(hc.parse_rows(text),
                         [hc.Row(1, "src/a.py", None, "a title", "warning")])


class TestAnswerFixLoop(unittest.TestCase):

    def test_only_row_applies_all(self):
        card = fix_loop_card(_rows(SEEDED + ("critical",)))
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers, {_q(card): hc.APPLY_ALL})
        self.assertEqual(d.questions_asked, 1)

    def test_among_others_applies_selected(self):
        card = fix_loop_card(_rows(NOISE_A + ("warning",),
                                   SEEDED + ("critical",)))
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers, {_q(card): hc.APPLY_SELECTED})

    def test_absent_fails(self):
        card = fix_loop_card(_rows(NOISE_A + ("warning",)))
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_SEEDED_NOT_LISTED)
        self.assertEqual(d.answers, {})

    def test_title_match_is_exact_not_substring(self):
        card = fix_loop_card(_rows((SEEDED[0], SEEDED[1] + " again",
                                    "critical")))
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_SEEDED_NOT_LISTED)

    def test_same_title_other_file_is_not_seeded(self):
        card = fix_loop_card(_rows(("src/other.py", SEEDED[1], "critical")))
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_SEEDED_NOT_LISTED)

    def test_compact_cut_title_matches_only_its_own_prefix(self):
        card = fix_loop_card(_rows(SEEDED + ("critical",)))
        q = card["questions"][0]
        head = q["question"].split("\n\n")[0]
        q["question"] = head + "\n\n#1 src/clamp.py:10 — clamp returns a… (critical)"
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        q["question"] = head + "\n\n#1 src/clamp.py:10 — clamp drops… (critical)"
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_SEEDED_NOT_LISTED)

    def test_two_matching_rows_fail(self):
        card = fix_loop_card(_rows(SEEDED + ("critical",),
                                   SEEDED + ("warning",)))
        d = hc.answer_card(hc.FIX_LOOP, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_SEEDED_AMBIGUOUS)


class TestAnswerSelect(unittest.TestCase):

    def test_picks_the_seeded_label_only(self):
        rows = _rows(NOISE_A + ("warning",), SEEDED + ("critical",),
                     NOISE_B + ("medium",))
        card = select_card(rows)
        d = hc.answer_card(hc.FIX_LOOP_SELECT, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(list(d.answers.values()), ["#2 src/clamp.py:20"])
        # The chosen label parses back to the seeded row in the plugin.
        parsed = batch_parse.parse_selection(rows,
                                             labels=list(d.answers.values()))
        self.assertEqual(parsed["rows"], [2])

    def test_seeded_in_second_question(self):
        rows = _rows(*([NOISE_A + ("warning",)] * 5 + [SEEDED + ("critical",)]))
        card = select_card(rows)
        self.assertEqual(len(card["questions"]), 2)
        d = hc.answer_card(hc.FIX_LOOP_SELECT, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers, {_q(card, 1): "#6 src/clamp.py:60"})
        self.assertEqual(d.questions_asked, 2)

    def test_absent_fails(self):
        card = select_card(_rows(NOISE_A + ("warning",),
                                 NOISE_B + ("critical",)))
        d = hc.answer_card(hc.FIX_LOOP_SELECT, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_SEEDED_NOT_LISTED)


class TestAnswerStop(unittest.TestCase):

    def test_close_out_only_after_resolution(self):
        card = stop_card()
        d = hc.answer_card(hc.STOP, card, seeded=SEEDED, seeded_resolved=True)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers, {_q(card): hc.CLOSE_OUT})
        d = hc.answer_card(hc.STOP, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_STOP_EARLY)
        self.assertEqual(d.answers, {})


class TestAnswerFinalize(unittest.TestCase):

    def test_only_row_fix_all(self):
        card = finalize_card(_rows(SEEDED + ("critical",)))
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers[_q(card)], hc.FIX_ALL)
        self.assertEqual(d.deferred_non_seeded, 0)
        self.assertEqual(d.questions_asked, 2)

    def test_seeded_among_others_fixes_it_and_defers_the_rest(self):
        card = finalize_card(_rows(NOISE_A + ("warning",),
                                   SEEDED + ("critical",),
                                   NOISE_B + ("medium",)))
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers[_q(card)],
                         "fix 2; defer 1,3 -- harness: not the seeded finding")
        self.assertEqual(d.answers[_q(card, 1)], hc.OUT_OF_SCOPE)
        self.assertEqual(d.deferred_non_seeded, 2)

    def test_seeded_not_open_defers_every_row(self):
        card = finalize_card(_rows(NOISE_A + ("warning",),
                                   NOISE_B + ("critical",)))
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        self.assertIsNone(d.fail)
        self.assertEqual(d.answers[_q(card)],
                         "defer 1,2 -- harness: not the seeded finding")
        self.assertEqual(d.deferred_non_seeded, 2)

    def test_no_rows_fails(self):
        card = finalize_card([])
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_NO_ROWS)

    def test_truncated_card_fails(self):
        card = finalize_card(_rows(SEEDED + ("critical",)))
        card["questions"][0]["question"] += "\n… and 3 more"
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_TRUNCATED)

    def test_generated_answers_parse_in_the_plugin(self):
        """Round trip through the real finalize grammar (52-04): the decision
        per row and the inline reason come back as the harness intended."""
        rows = _rows(NOISE_A + ("warning",), SEEDED + ("critical",),
                     NOISE_B + ("medium",))
        card = finalize_card(rows)
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        got = batch_parse.parse_answer(rows, d.answers[_q(card)],
                                       d.answers[_q(card, 1)])
        self.assertIsInstance(got, dict, got)
        self.assertEqual(got["fix"], [rows[1]["stable_hash"]])
        self.assertEqual(got["defer"], [rows[0]["stable_hash"],
                                        rows[2]["stable_hash"]])
        self.assertEqual(got["dismiss"], [])
        self.assertEqual(got["undecided"], [])
        self.assertEqual(got["reason"], hc.DEFER_REASON)
        self.assertEqual(got["reason"], "harness: not the seeded finding")

        # Seeded already fixed: every remaining row is deferred, critical
        # included (named by number, so the mediums-only `rest` rule does
        # not leave it open).
        rest = _rows(NOISE_A + ("warning",), NOISE_B + ("critical",))
        card = finalize_card(rest)
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        got = batch_parse.parse_answer(rest, d.answers[_q(card)],
                                       d.answers[_q(card, 1)])
        self.assertEqual(got["defer"], [r["stable_hash"] for r in rest])
        self.assertEqual(got["undecided"], [])
        self.assertEqual(got["reason"], hc.DEFER_REASON)

        # Only the seeded row: the Fix all button fixes it.
        one = _rows(SEEDED + ("warning",))
        card = finalize_card(one)
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        got = batch_parse.parse_answer(one, d.answers[_q(card)],
                                       d.answers[_q(card, 1)])
        self.assertEqual(got["fix"], [one[0]["stable_hash"]])
        self.assertIsNone(got["reason"])

    def test_round_trip_without_q2_still_has_a_reason(self):
        rows = _rows(NOISE_A + ("warning",), SEEDED + ("critical",))
        card = finalize_card(rows, with_q2=False)
        d = hc.answer_card(hc.FINALIZE, card, seeded=SEEDED)
        got = batch_parse.parse_answer(rows, d.answers[_q(card)], None)
        self.assertEqual(got["reason"], hc.DEFER_REASON)
        self.assertEqual(d.questions_asked, 1)


class TestAnswerUnknown(unittest.TestCase):

    def _first_run_answer(self):
        card = first_run_card()
        return hc.answer_card(hc.classify_card(card), card, seeded=SEEDED)

    def test_first_run_card_fails(self):
        d = self._first_run_answer()
        self.assertEqual(d.fail, hc.FAIL_UNEXPECTED_CARD)
        self.assertEqual(d.answers, {})
        self.assertEqual(d.questions_asked, 1)

    def test_estimate_card_fails(self):
        card = estimate_card()
        d = hc.answer_card(hc.classify_card(card), card, seeded=SEEDED)
        self.assertEqual(d.fail, hc.FAIL_UNEXPECTED_CARD)

    def test_mutant_unknown_answers_first_option(self):
        """Mutant: the UNKNOWN branch guesses the first option. The control
        above must flip from failed to answered."""
        def guess(input_data, seeded, seeded_resolved):
            q = input_data["questions"][0]
            return {q["question"]: q["options"][0]["label"]}, 0, None

        with mock.patch.dict(hc._ANSWERERS, {hc.UNKNOWN: guess}):
            d = self._first_run_answer()
        self.assertIsNone(d.fail)
        self.assertEqual(list(d.answers.values()), ["Yes, move it"])


class TestSeededIdentityOnly(unittest.TestCase):

    def _cards(self):
        rows = _rows(NOISE_A + ("warning",), SEEDED + ("critical",))
        return rows, select_card(rows), finalize_card(rows)

    def _answers(self):
        rows, sel, fin = self._cards()
        return (hc.answer_card(hc.FIX_LOOP_SELECT, sel, seeded=SEEDED),
                hc.answer_card(hc.FINALIZE, fin, seeded=SEEDED))

    def test_seeded_row_two_is_chosen(self):
        sel, fin = self._answers()
        self.assertEqual(list(sel.answers.values()), ["#2 src/clamp.py:20"])
        self.assertTrue(list(fin.answers.values())[0].startswith("fix 2;"))

    def test_mutant_answers_from_detection_row_one(self):
        """Mutant: answer from the first detection row instead of the seeded
        identity. The control above must flip to row 1."""
        def first_row(rows, seeded):
            return (rows[0] if rows else None), None

        with mock.patch.object(hc, "_find_seeded", first_row):
            sel, fin = self._answers()
        self.assertEqual(list(sel.answers.values()), ["#1 src/util.py:10"])
        self.assertTrue(list(fin.answers.values())[0].startswith("fix 1;"))


class TestClassifyTurnEnd(unittest.TestCase):

    def test_plugin_one_liners(self):
        cases = [
            ("No changes to review.", hc.NO_CHANGES),
            ("✓ Phase 0 — Resolve scope\nNo changes to review.",
             hc.NO_CHANGES),
            ("No new changes since pass 2.", hc.NO_NEW_CHANGES),
            ("✅ No issues to fix. Re-run when you've changed code, or run "
             "with `--finalize` to ship.", hc.NO_ISSUES),
            ("Paused. Resume with `/vibe-check:review ` or close out later "
             "with `--finalize`.", hc.PAUSED),
            ("Paused. Resume with `/vibe-check:deep-review 52` or close out "
             "later with `--finalize`.", hc.PAUSED),
            ("Wrote `.turingmind/REVIEW.md`. It is gitignored — `cp` it if "
             "you want it tracked.", hc.REVIEW_WRITTEN),
        ]
        for text, kind in cases:
            with self.subTest(text=text):
                self.assertEqual(hc.classify_turn_end(text), kind)

    def test_unknown_text_is_a_would_be_question(self):
        for text in ("", None, "Shall I proceed with the fix?",
                     "Paused for your edits. Commit them, then reply `done` "
                     "and I'll rerun the review.",
                     "No changes to review.\nWant me to run --finalize?",
                     "No changes to review. No issues to fix.",
                     "No new changes since pass two.",
                     "Wrote .turingmind/REVIEW.md."):
            with self.subTest(text=text):
                self.assertEqual(hc.classify_turn_end(text), hc.UNKNOWN)


class TestNextOwnerCommand(unittest.TestCase):

    def test_finalize_after_one_liners(self):
        for kind in (hc.NO_CHANGES, hc.NO_NEW_CHANGES, hc.NO_ISSUES):
            with self.subTest(kind=kind):
                self.assertEqual(hc.next_owner_command(kind, "review"),
                                 hc.Next("/vibe-check:review --finalize",
                                         None))
        self.assertEqual(
            hc.next_owner_command(hc.NO_CHANGES, "deep-review"),
            hc.Next("/vibe-check:deep-review --finalize", None))

    def test_done_and_failures(self):
        self.assertEqual(hc.next_owner_command(hc.REVIEW_WRITTEN, "review"),
                         hc.Next(None, None))
        self.assertEqual(hc.next_owner_command(hc.PAUSED, "review").fail,
                         hc.FAIL_PAUSED)
        self.assertEqual(hc.next_owner_command(hc.UNKNOWN, "review").fail,
                         hc.FAIL_TURN_END)

    def test_bad_mode(self):
        with self.assertRaises(ValueError):
            hc.next_owner_command(hc.NO_CHANGES, "review; rm -rf /")


if __name__ == "__main__":
    unittest.main()
