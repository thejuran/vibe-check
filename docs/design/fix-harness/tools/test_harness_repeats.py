"""Tests for harness_repeats: card keys, evidence fingerprints and the
question ledger that fails a run on a repeat or on exhausted retries.

Run with bare `pytest -q` from this directory.
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_repeats as hr  # noqa: E402

ROW_SEEDED = (2, "src/clamp.py", 20, "clamp returns a value above the bound",
              "critical")
ROW_NOISE = (1, "src/util.py", 10, "unused import", "warning")

STATUS = ("1 .M N... 100644 100644 100644 aaa bbb src/util.py\0"
          "? notes.txt\0")
STATUS_WITH_TOOL = STATUS + "? .turingmind/\0" + (
    "1 .M N... 100644 100644 100644 ccc ddd .turingmind/state/x.json\0")


def _key(kind="fix-loop", rows=(ROW_SEEDED,), text="Pass 2 — 1 finding(s)"):
    return hr.card_key(kind, rows, text)


def _ev(head="a" * 40, status=STATUS, state=b'{"passes": []}'):
    return hr.evidence_fingerprint(head, status, state)


class TestCardKey(unittest.TestCase):

    def test_pass_numbers_do_not_change_the_key(self):
        self.assertEqual(
            _key(text="Pass 2 — 1 finding(s) (1 unchanged since pass 1)"),
            _key(text="Pass 3 — 1 finding(s) (1 unchanged since pass 2)"))

    def test_rows_kind_and_text_change_the_key(self):
        base = _key()
        self.assertNotEqual(base, _key(rows=(ROW_SEEDED, ROW_NOISE)))
        self.assertNotEqual(base, _key(kind="finalize"))
        self.assertNotEqual(base, _key(text="Pass 2 — 2 finding(s)"))

    def test_row_order_and_numbers_do_not_change_the_key(self):
        renumbered = (1,) + ROW_SEEDED[1:]
        self.assertEqual(_key(rows=(ROW_SEEDED, ROW_NOISE)),
                         _key(rows=(ROW_NOISE, renumbered)))


class TestEvidenceFingerprint(unittest.TestCase):

    def test_tool_paths_are_ignored(self):
        self.assertEqual(_ev(status=STATUS), _ev(status=STATUS_WITH_TOOL))
        self.assertEqual(_ev(status=STATUS.replace("\0", "\n")),
                         _ev(status=STATUS))

    def test_each_input_is_evidence(self):
        base = _ev()
        self.assertNotEqual(base, _ev(head="b" * 40))
        self.assertNotEqual(base, _ev(status="? other.txt\0"))
        self.assertNotEqual(base, _ev(state=b'{"passes": [1]}'))
        self.assertEqual(len(base), 64)

    def test_fields_do_not_run_together(self):
        self.assertNotEqual(hr.evidence_fingerprint("ab", "", b"c"),
                            hr.evidence_fingerprint("a", "", b"bc"))


class TestLedger(unittest.TestCase):

    def _exact_repeat(self, ledger):
        first = ledger.observe(_key(), _ev(), "Apply all & rerun")
        second = ledger.observe(_key(), _ev(), "Apply all & rerun")
        return first, second

    def test_exact_repeat_fails(self):
        ledger = hr.Ledger()
        self.assertEqual(self._exact_repeat(ledger), (hr.OK, hr.REPEAT))
        self.assertEqual(ledger.repeats, 1)
        self.assertEqual(ledger.total_questions, 2)

    def test_mutant_evidence_always_differs(self):
        """Mutant: evidence comparison always reports a change. The exact
        repeat above must flip to ok."""
        with mock.patch.object(hr, "_same_evidence", lambda a, b: False):
            self.assertEqual(self._exact_repeat(hr.Ledger()), (hr.OK, hr.OK))

    def test_reask_after_material_change_is_counted_not_failed(self):
        ledger = hr.Ledger()
        self.assertEqual(ledger.observe(_key(), _ev(), "x"), hr.OK)
        self.assertEqual(ledger.observe(_key(), _ev(head="b" * 40), "x"),
                         hr.OK)
        self.assertEqual(ledger.total_questions, 2)
        self.assertEqual(ledger.by_kind["fix-loop"], 2)
        self.assertEqual(ledger.repeats, 0)
        # Back to evidence already answered: that is a repeat.
        self.assertEqual(ledger.observe(_key(), _ev(), "x"), hr.REPEAT)

    def test_questions_count_every_question_in_a_payload(self):
        ledger = hr.Ledger()
        ledger.observe(_key(kind="finalize"), _ev(), "fix 1", questions=2)
        self.assertEqual(ledger.total_questions, 2)
        self.assertEqual(ledger.cards, 1)

    def _same_kind_run(self, ledger):
        return [ledger.observe(_key(text="card %d" % i), _ev(), "x")
                for i in range(5)]

    def test_fifth_same_kind_card_is_exhausted(self):
        got = self._same_kind_run(hr.Ledger())
        self.assertEqual(got, [hr.OK] * 4 + [hr.EXHAUSTED])

    def test_mutant_same_kind_bound_raised(self):
        """Mutant: max_same_kind raised to 100. The fifth card must flip
        from exhausted to ok."""
        got = self._same_kind_run(hr.Ledger(max_same_kind=100))
        self.assertEqual(got[-1], hr.OK)

    def test_total_bound(self):
        ledger = hr.Ledger()
        kinds = ["fix-loop", "fix-loop-select", "stop", "finalize"]
        got = [ledger.observe(_key(kind=kinds[i % 4], text="c%d" % i), _ev(),
                              "x") for i in range(13)]
        self.assertEqual(got, [hr.OK] * 12 + [hr.EXHAUSTED])
        got = hr.Ledger(max_total=100, max_same_kind=100)
        self.assertEqual(
            [got.observe(_key(kind=kinds[i % 4], text="c%d" % i), _ev(), "x")
             for i in range(13)][-1], hr.OK)

    def test_bounds_must_be_positive(self):
        for kwargs in ({"max_total": 0}, {"max_same_kind": 0},
                       {"max_total": True}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    hr.Ledger(**kwargs)


class TestFixLoopAfterFinalize(unittest.TestCase):

    def _ledger(self):
        ledger = hr.Ledger()
        ledger.observe(_key(kind="finalize", rows=(ROW_NOISE, ROW_SEEDED)),
                       _ev(), "fix 2; defer 1 -- r", questions=2,
                       fixed_rows=(ROW_SEEDED,))
        return ledger

    def test_reasking_fixed_rows_with_same_evidence_is_a_repeat(self):
        ledger = self._ledger()
        self.assertEqual(
            ledger.observe_fix_loop_after_finalize((ROW_SEEDED,), _ev()),
            hr.REPEAT)
        self.assertEqual(ledger.repeats, 1)

    def test_changed_evidence_or_new_rows_are_not_repeats(self):
        ledger = self._ledger()
        self.assertEqual(
            ledger.observe_fix_loop_after_finalize((ROW_SEEDED,),
                                                   _ev(head="b" * 40)),
            hr.OK)
        self.assertEqual(
            ledger.observe_fix_loop_after_finalize((ROW_SEEDED, ROW_NOISE),
                                                   _ev()),
            hr.OK)
        self.assertEqual(ledger.observe_fix_loop_after_finalize((), _ev()),
                         hr.OK)
        self.assertEqual(ledger.repeats, 0)


if __name__ == "__main__":
    unittest.main()
