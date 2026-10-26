"""test_card_text.py — the numbered list the owner reads ON the card.

`batch_card.py rows` renders `card_text`, which the prose copies verbatim into
the AskUserQuestion question: text printed only inside a Bash call's output
is collapsed by the terminal and the owner never sees it. `parse` renders
`echo_text`, which the prose puts where the owner sees it. These tests pin
the exact rendering, the one-line flattening of diff-authored text, the card
budget and the agreement between the prose's documented formats and the
helper's output. Each lock carries a mutant subtest proving it can trip.
"""

import copy
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module under test)
from test_batch_card import (  # noqa: E402
    TempDirCase, dismiss, ordering_state, run_cli)
from test_carry_state import (  # noqa: E402
    F, HA, HB, ba_row_state, ba_state, member_ref, mk_finding, mk_pass,
    mk_state, snap)

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
FIX_LOOP_MD = os.path.join(PLUGIN_DIR, "phases", "review", "50-fix-loop.md")
FINALIZE_MD = os.path.join(PLUGIN_DIR, "phases", "shared", "90-finalize.md")


def doc_of(state, mode="fix-loop", head_blobs=None, subset=None):
    doc, reason = batch_card.build_rows(state, mode, head_blobs, subset)
    assert reason is None, reason
    return doc


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def severity_stale_state():
    decided = dismiss(ba_row_state(row_band="warning", a_band="medium"), HA,
                      reason="Accepted risk")
    s = copy.deepcopy(decided)
    # A rise backed by a lane absent at decision time (`security` now
    # reports A itself).
    s["passes"] = ba_row_state(row_band="warning", a_band="warning",
                               lanes=("bugs", "security"))["passes"]
    return s


def legacy_severity_state():
    """The same rise on a decision saved without a reviewer list (written
    before reviewer lanes were recorded): it re-asks, with no lane to name."""
    s = severity_stale_state()
    del s["decisions"][HA]["attribution"]
    del s["decisions"][HA]["lanes"]
    return s


def nearby_stale_state():
    decided = dismiss(ba_state(), HA, reason="Guarded")
    s = copy.deepcopy(decided)
    s["passes"] = ba_state(a_snapshot=dict(snap(1, line=11),
                                           nearby_at=2))["passes"]
    return s


def two_lane_rise_state():
    decided = dismiss(ba_row_state(row_band="warning", a_band="medium"), HA,
                      reason="Accepted risk")
    s = copy.deepcopy(decided)
    s["passes"] = ba_row_state(row_band="warning", a_band="warning",
                               lanes=("bugs", "security", "perf"))["passes"]
    return s


def joined_note_state(covered_extra=0, lanes=("security",), kind="dismiss"):
    """Row HB dismissed with its own member record plus `covered_extra`
    covered members; on the next pass new concerns from `lanes` join it."""
    def row(extra):
        members = [member_ref(title="t bbbbbb")]
        members += [member_ref(line=20 + i, title="K%d" % i)
                    for i in range(covered_extra)]
        return mk_finding("warning", "persisted", HB, members=members + extra)
    decided = dismiss(mk_state([mk_pass(1, []), mk_pass(2, [row([])])]), HB,
                      reason="Guarded upstream", decision=kind)
    s = copy.deepcopy(decided)
    joiners = [dict(member_ref(line=30 + i, title="N%d" % i), agent=lane)
               for i, lane in enumerate(lanes)]
    s["passes"] = [mk_pass(1, []), mk_pass(2, [row(joiners)])]
    return s


def compact_text(state):
    return batch_card._render(doc_of(state)["rows"], "fix-loop",
                              compact=True)


def code_stale_state():
    # Phase 57 D-01: a line move alone no longer re-asks, so the code-stale
    # case is a failed relocation (null canonical text in the snapshot).
    decided = dismiss(ba_state(a_snapshot=snap(1, line=11)), HA,
                      reason="Out of scope")
    s = copy.deepcopy(decided)
    s["passes"] = ba_state(a_snapshot=dict(
        snap(1, line=14), canonical_line_content=None))["passes"]
    return s


def long_state(count, title_len=150, problem_len=200):
    findings = [mk_finding("warning", "new", "%064x" % (i + 1),
                           file="app/f%02d.py" % i, line=i + 1,
                           title="T%02d " % i + "x" * title_len,
                           problem="P" * problem_len)
                for i in range(count)]
    return mk_state([mk_pass(1, []), mk_pass(2, findings)])


class TestCardTextRendering(unittest.TestCase):

    def test_fix_loop_plain_rows_exact(self):
        doc = doc_of(ordering_state())
        self.assertEqual(doc["card_text"], "\n".join([
            "#1 app/z.py:3 — t bbbbbb (critical)",
            "#2 app/a.py:20 — t dddddd (warning)",
            "#3 app/a.py:9 — t aaaaaa (medium)",
        ]))
        self.assertEqual(doc["list_text"], doc["card_text"])
        self.assertFalse(doc["card_text_truncated"])

    def test_absorbed_and_pending_suffixes_in_order(self):
        doc = doc_of(ba_state(a_snapshot=snap(1, line=11)))
        self.assertEqual(doc["card_text"].splitlines(), [
            "#1 %s:10 — t bbbbbb (warning)" % F,
            "#2 %s:11 — A (warning) (absorbed into \"t bbbbbb\" — decided "
            "on its own) — unchanged since pass 1, decision pending" % F,
        ])

    def test_severity_rise_names_lane_exact(self):
        text = doc_of(severity_stale_state())["card_text"]
        self.assertIn(
            " — severity rose (medium → warning) since your decision on "
            "pass 2: security now also reports it (was: dismissed — "
            "Accepted risk)", text)
        text = doc_of(two_lane_rise_state())["card_text"]
        self.assertIn(
            " — severity rose (medium → warning) since your decision on "
            "pass 2: perf, security now also report it (was: dismissed — "
            "Accepted risk)", text)

    def test_severity_changed_unchanged_without_gained(self):
        text = doc_of(legacy_severity_state())["card_text"]
        self.assertIn(
            " — severity changed (medium → warning) since your decision on "
            "pass 2 (was: dismissed — Accepted risk)", text)
        self.assertNotIn("severity rose", text)

    def test_nearby_stale_suffix_exact(self):
        text = doc_of(nearby_stale_state())["card_text"]
        self.assertIn(" — code next to it changed since your decision on "
                      "pass 2 (was: dismissed — Guarded)", text)

    def test_joined_note_exact(self):
        text = doc_of(joined_note_state())["card_text"]
        self.assertIn(" — 1 finding here already dismissed (your reason: "
                      "Guarded upstream); a new concern from security "
                      "joined it", text)
        text = doc_of(joined_note_state(covered_extra=2,
                                        lanes=("security", "perf"),
                                        kind="defer"))["card_text"]
        self.assertIn(" — 3 findings here already deferred (your reason: "
                      "Guarded upstream); new concerns from perf, security "
                      "joined it", text)

    def test_inherited_severity_rise_suffix_exact(self):
        from test_batch_card import inherited_state
        s, _ = inherited_state("rise")
        self.assertIn(
            " — severity rose (warning → critical) since your decision on "
            "pass 1: security now also reports it (was: dismissed — "
            "not a bug)", doc_of(s)["card_text"])
        text = compact_text(s)
        self.assertIn(" — severity rose since your decision on pass 1", text)
        self.assertNotIn("(was:", text)

    def test_inherited_joined_note_exact(self):
        from test_batch_card import inherited_state
        s, _ = inherited_state("joined")
        self.assertIn(
            " — 1 finding here already dismissed (your reason: not a bug); "
            "a new concern from security joined it", doc_of(s)["card_text"])
        text = compact_text(s)
        self.assertIn(" — 1 finding here already dismissed; a new concern "
                      "from security joined it", text)
        self.assertNotIn("your reason", text)

    def test_compact_stale_forms_exact(self):
        cases = (
            (nearby_stale_state(),
             " — code next to it changed since your decision on pass 2"),
            (severity_stale_state(),
             " — severity rose since your decision on pass 2"),
            (legacy_severity_state(),
             " — severity changed since your decision on pass 2"),
            (joined_note_state(),
             " — 1 finding here already dismissed; a new concern from "
             "security joined it"),
        )
        for state, phrase in cases:
            with self.subTest(phrase=phrase):
                text = compact_text(state)
                self.assertTrue(text.endswith(phrase) or phrase + "\n"
                                in text, text)
                self.assertNotIn("(was:", text)
                self.assertNotIn("your reason", text)

    def test_stale_suffix_values_are_flattened(self):
        """Lane names and reasons are data: each is flattened to one line,
        so none can start a fake row."""
        s = joined_note_state(lanes=("sec\n#9 evil.py:1 — x",))
        s["decisions"][HB]["reason"] = "r1\n#8 fake"
        text = doc_of(s)["card_text"]
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("a new concern from sec #9 evil.py:1 — x joined it",
                      text)
        s = severity_stale_state()
        row_a = [f for f in s["passes"][-1]["findings"]
                 if f["stable_hash"] == HA][0]
        row_a["members"][1]["agent"] = "lane\r\n#7 x"
        text = doc_of(s)["card_text"]
        self.assertEqual(len(text.splitlines()), 2)
        self.assertIn("lane #7 x now also reports it", text)

    def test_code_stale_suffix_exact(self):
        text = doc_of(code_stale_state())["card_text"]
        self.assertIn(" — code changed since your decision on pass 2 "
                      "(was: dismissed — Out of scope)", text)

    def test_finalize_problem_line_first_line_cut_to_120(self):
        s = ordering_state()
        s["passes"][-1]["findings"][1]["problem"] = (
            "Q" * 130 + "\nsecond line never shown")
        doc = doc_of(s, "finalize", {})
        lines = doc["card_text"].splitlines()
        self.assertEqual(lines[0], "#1 app/z.py:3 — t bbbbbb (critical)")
        self.assertEqual(lines[1], "    " + "Q" * 120)
        self.assertNotIn("second line", doc["card_text"])
        # A row with no problem gets no indented line.
        self.assertFalse(lines[2].startswith("    "))

    def test_fix_loop_has_no_problem_line(self):
        s = ordering_state()
        s["passes"][-1]["findings"][1]["problem"] = "SHOULD NOT SHOW"
        self.assertNotIn("SHOULD NOT SHOW", doc_of(s)["card_text"])

    def test_subset_routing_and_closed_lead(self):
        s = dismiss(ba_state(), HB)
        doc = doc_of(s, subset=[HA])
        self.assertEqual(doc["card_text"].splitlines()[0].split(" — ", 1)[1],
                         'fixing absorbed "A" (routed through "t bbbbbb", '
                         "which is not being fixed) (your earlier decision "
                         "on this row stays)")
        doc = doc_of(ba_state(), subset=[HB, HA])
        self.assertIn(' — also fixing absorbed "A" through this row',
                      doc["card_text"])

    def test_diff_text_cannot_fake_a_row(self):
        """A title or path carrying line breaks or control characters is
        flattened to one line, so it can never start a fake `#n` row."""
        s = ordering_state()
        s["passes"][-1]["findings"][1]["title"] = (
            "real\n#9 evil.py:1 — fake row (critical) x\x1b[2J")
        s["passes"][-1]["findings"][0]["file"] = "app/a\r\n#8.py"
        text = doc_of(s)["card_text"]
        self.assertEqual(len(text.splitlines()), 3)
        for line in text.splitlines():
            self.assertRegex(line, r"^#[123] ")
        self.assertNotIn("\x1b", text)
        with self.subTest("mutant: no flattening"):
            with mock.patch.object(batch_card, "_one_line",
                                   lambda v: v if isinstance(v, str) else ""):
                mutant = doc_of(s)["card_text"]
            self.assertGreater(len(mutant.splitlines()), 3)


class TestCardBudget(unittest.TestCase):

    def test_under_budget_is_full(self):
        doc = doc_of(long_state(3), "finalize", {})
        self.assertLessEqual(len(doc["card_text"]),
                             batch_card.CARD_TEXT_MAX_CHARS)
        self.assertEqual(doc["card_text"], doc["list_text"])

    def test_compact_when_full_does_not_fit(self):
        doc = doc_of(long_state(10), "finalize", {})
        self.assertGreater(len(doc["list_text"]),
                           batch_card.CARD_TEXT_MAX_CHARS)
        self.assertLessEqual(len(doc["card_text"]),
                             batch_card.CARD_TEXT_MAX_CHARS)
        self.assertFalse(doc["card_text_truncated"])
        lines = doc["card_text"].splitlines()
        self.assertEqual(len(lines), 10)  # no problem lines
        self.assertTrue(all(line.startswith("#") for line in lines))
        self.assertIn("…", lines[0])  # title cut

    def test_truncated_when_compact_does_not_fit(self):
        doc = doc_of(long_state(40), "fix-loop")
        text = doc["card_text"]
        self.assertTrue(doc["card_text_truncated"])
        self.assertLessEqual(len(text), batch_card.CARD_TEXT_MAX_CHARS)
        lines = text.splitlines()
        kept = len(lines) - 1
        self.assertGreater(kept, 0)
        self.assertEqual(
            lines[-1], "… and %d more (#%d-#40) — the full list is printed "
            "above this card." % (40 - kept, kept + 1))
        # The kept rows are the first rows, in order.
        for i, line in enumerate(lines[:-1]):
            self.assertTrue(line.startswith("#%d " % (i + 1)))
        # The full list still carries every row.
        self.assertEqual(len(doc["list_text"].splitlines()), 40)
        with self.subTest("mutant: no budget"):
            unbounded = batch_card.card_texts(
                doc["rows"], "fix-loop", limit=10 ** 9)
            self.assertGreater(len(unbounded["card_text"]),
                               batch_card.CARD_TEXT_MAX_CHARS)

    def test_one_huge_row_still_bounded(self):
        rows = doc_of(long_state(2, title_len=50))["rows"]
        out = batch_card.card_texts(rows, "fix-loop", limit=60)
        self.assertTrue(out["card_text_truncated"])
        self.assertEqual(out["card_text"].splitlines()[-1][:10],
                         "… and 2 mo")

    def test_empty_rows(self):
        self.assertEqual(batch_card.card_texts([], "finalize"),
                         {"card_text": "", "list_text": "",
                          "card_text_truncated": False})


class TestCliAndEcho(TempDirCase):

    def test_cli_rows_carries_card_text(self):
        proc = run_cli(["rows", "--mode", "fix-loop"],
                       json.dumps(ordering_state()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        doc = json.loads(proc.stdout)
        self.assertTrue(doc["card_text"].startswith("#1 app/z.py:3 — "))
        self.assertIn("list_text", doc)
        self.assertIs(doc["card_text_truncated"], False)

    def test_rows_doc_with_card_text_still_valid_for_answer_side(self):
        doc = doc_of(ordering_state())
        self.assertTrue(batch_card._valid_rows_doc(doc))

    def parse(self, answer):
        rows = self.write("rows.json", doc_of(ordering_state()))
        proc = run_cli(["parse", "--rows", rows,
                        "--answer", self.write("a.json", answer)])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        return json.loads(proc.stdout)

    def test_echo_text_joins_echo_and_reason(self):
        out = self.parse({"q1": "fix 2; dismiss rest", "q2": "False positive"})
        self.assertEqual(out["echo_text"],
                         "\n".join(out["echo"] + ["Reason: False positive"]))
        self.assertTrue(out["echo"])

    def test_echo_text_reason_is_one_line(self):
        out = self.parse({"q1": "dismiss 3", "q2": "line one\nline two"})
        self.assertEqual(out["echo_text"].splitlines()[-1],
                         "Reason: line one line two")

    def test_echo_text_without_reason(self):
        out = self.parse({"q1": "Fix all", "q2": None})
        self.assertNotIn("Reason:", out["echo_text"])
        self.assertEqual(out["echo_text"], "\n".join(out["echo"]))


class TestProseMatchesHelper(unittest.TestCase):
    """Every suffix format the prose documents is what the helper renders."""

    def fill(self, template, **values):
        for key, value in values.items():
            template = template.replace("{{%s}}" % key, str(value))
        self.assertNotIn("{{", template)
        return template

    def suffixes(self):
        return {
            "pending": (ba_state(a_snapshot=snap(1, line=11)),
                        " — unchanged since pass {{pending_since}}, decision "
                        "pending", {"pending_since": 1}),
            "absorbed": (ba_state(),
                         ' (absorbed into "{{lead_title}}" — decided on its '
                         "own)", {"lead_title": "t bbbbbb"}),
            "severity": (legacy_severity_state(),
                         " — severity changed ({{stale.was_band}} → {{band}}) "
                         "since your decision on pass {{stale.at_pass}} (was: "
                         "{{dismissed|deferred}} — {{stale.reason}})",
                         {"stale.was_band": "medium", "band": "warning",
                          "stale.at_pass": 2, "dismissed|deferred":
                          "dismissed", "stale.reason": "Accepted risk"}),
            "nearby": (nearby_stale_state(),
                       " — code next to it changed since your decision on "
                       "pass {{stale.at_pass}} (was: {{dismissed|deferred}} "
                       "— {{stale.reason}})",
                       {"stale.at_pass": 2, "dismissed|deferred":
                        "dismissed", "stale.reason": "Guarded"}),
            "code": (code_stale_state(),
                     " — code changed since your decision on pass "
                     "{{stale.at_pass}} (was: {{dismissed|deferred}} — "
                     "{{stale.reason}})",
                     {"stale.at_pass": 2, "dismissed|deferred": "dismissed",
                      "stale.reason": "Out of scope"}),
        }

    def test_documented_suffixes_render(self):
        prose = {"fix-loop": read(FIX_LOOP_MD), "finalize": read(FINALIZE_MD)}
        for name, (state, template, values) in self.suffixes().items():
            for mode, text in prose.items():
                with self.subTest(suffix=name, mode=mode):
                    self.assertIn(template, text)
                    rendered = doc_of(state, mode,
                                      {} if mode == "finalize" else None)
                    self.assertIn(self.fill(template, **values),
                                  rendered["card_text"])

    def test_agreement_trips_on_helper_drift(self):
        state, template, values = self.suffixes()["pending"]
        with mock.patch.object(batch_card, "_suffixes",
                               lambda row, compact: " — pending"):
            rendered = doc_of(state)["card_text"]
        self.assertNotIn(self.fill(template, **values), rendered)


if __name__ == "__main__":
    unittest.main()
