"""test_card_scope.py — the bulk-fix option says exactly what it does.

"Apply all & rerun" (fix-loop card) and "Fix all" (Finalize card) never send
a needs-verification row: `select(rows, {"all": true})` drops them and the
Finalize `fix rest` reaches only `_rest_bands_for("fix")`. The cards used to
describe these options as covering every row (K2), so the owner could not tell
which rows were left out.

`batch_card.py rows` now renders `nv_rows` (the row numbers the bulk-fix
option leaves out) and `bulk_fix_text` (the option description naming them by
number). These tests lock the text to the behavior: the numbers named in the
text equal `nv_rows`, equal the needs-verification rows on the card, and
equal the rows the select/parse path actually leaves out — for both cards.
A subset card (every row already named by the owner) excludes nothing. Each
lock carries a mutant subtest proving it can trip.
"""

import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module under test)
import batch_parse  # noqa: E402  (sibling module: Finalize `fix rest` bands)
import carry_state  # noqa: E402  (sibling module: NV_BAND)
from test_batch_card import HC, HD, HE, nv_card_state  # noqa: E402
from test_card_text import doc_of  # noqa: E402
from test_carry_state import HA, HB, mk_finding, mk_pass, mk_state  # noqa: E402

FIX_LOOP_TEXT_PREFIX = "every listed row"
FINALIZE_TEXT_PREFIX = "Fix every critical, warning and medium row"

# The exact descriptions for nv_card_state() (NV rows #3 and #4) and for a
# card with one NV row (#2). 58-04 / 58-05 copy `{{bulk_fix_text}}` verbatim.
FIX_LOOP_TEXT_TWO = (
    "every listed row except Needs-verification rows #3, #4 — confirm, "
    "dismiss or defer those by number in Other (`fix N`, `dismiss N -- "
    "reason`, `defer N -- reason`)")
FINALIZE_TEXT_TWO = (
    "Fix every critical, warning and medium row. Needs-verification rows "
    "(#3, #4) are not included — name them by number in Mixed…")
FIX_LOOP_TEXT_ONE = (
    "every listed row except Needs-verification row #2 — confirm, dismiss "
    "or defer it by number in Other (`fix N`, `dismiss N -- reason`, "
    "`defer N -- reason`)")
FINALIZE_TEXT_ONE = (
    "Fix every critical, warning and medium row. Needs-verification row "
    "(#2) is not included — name it by number in Mixed…")
FIX_LOOP_TEXT_NONE = "every listed row"
FINALIZE_TEXT_NONE = "Fix every critical, warning and medium row."

NUMBER_RE = re.compile(r"#(\d+)")


def finalize_doc(state):
    return doc_of(state, "finalize", {})


def no_nv_state():
    rows = [mk_finding("critical", "new", HB, file="app/z.py", line=3),
            mk_finding("medium", "new", HC, file="app/a.py", line=9),
            mk_finding("warning", "new", HD, file="app/a.py", line=20)]
    return mk_state([mk_pass(1, []), mk_pass(2, rows)])


def one_nv_state():
    rows = [mk_finding("critical", "new", HB, file="app/z.py", line=3),
            mk_finding("needs-verification", "new", HA, file="a.py",
                       line=12),
            mk_finding("medium", "new", HC, file="app/a.py", line=9)]
    return mk_state([mk_pass(1, []), mk_pass(2, rows)])


def nv_by_band(doc):
    return [r["n"] for r in doc["rows"] if r["band"] == carry_state.NV_BAND]


def named_in_text(doc):
    """The row numbers the bulk-fix description names."""
    return sorted(int(n) for n in NUMBER_RE.findall(doc["bulk_fix_text"]))


def excluded_by_behavior(doc, mode):
    """The row numbers the bulk-fix option actually leaves out.

    fix-loop: "Apply all & rerun" is `select(rows, {"all": true})` (subset
    cards pass subset=True). finalize: "Fix all" is `parse(doc, {"q1": "Fix
    all"})`, whose fix_targets are the hashes sent to the fix loop.
    """
    every = sorted(r["n"] for r in doc["rows"])
    if mode == "fix-loop":
        chosen, reason = batch_card.select(doc["rows"], {"all": True},
                                           subset=bool(doc.get("subset")))
        assert reason is None, reason
        sent = set(chosen["rows"])
    else:
        result, reason = batch_card.parse(doc, {"q1": "Fix all", "q2": None})
        assert reason is None, reason
        by_hash = {r["stable_hash"]: r["n"] for r in doc["rows"]}
        sent = {by_hash[h] for h in result["fix_targets"]}
    return [n for n in every if n not in sent]


def lock_holds(doc, mode):
    """Text == nv_rows == behavior (and == NV band rows off a subset card)."""
    behavior = excluded_by_behavior(doc, mode)
    if named_in_text(doc) != doc["nv_rows"] or doc["nv_rows"] != behavior:
        return False
    if doc.get("subset"):
        return doc["nv_rows"] == [] and "Needs-verification" not in \
            doc["bulk_fix_text"]
    return doc["nv_rows"] == nv_by_band(doc)


class TestFixture(unittest.TestCase):
    """The fixtures carry what the locks assume they carry."""

    def test_fixture_bands(self):
        for mode, doc in (("fix-loop", doc_of(nv_card_state())),
                          ("finalize", finalize_doc(nv_card_state()))):
            with self.subTest(mode=mode):
                bands = [r["band"] for r in doc["rows"]]
                self.assertGreaterEqual(bands.count(carry_state.NV_BAND), 2)
                for band in ("critical", "warning", "medium"):
                    self.assertGreaterEqual(bands.count(band), 1, band)
                self.assertEqual(nv_by_band(doc), [3, 4])
        self.assertEqual(
            [r["band"] for r in doc_of(no_nv_state())["rows"]],
            ["critical", "warning", "medium"])
        self.assertEqual(nv_by_band(doc_of(one_nv_state())), [2])
        subset = doc_of(nv_card_state(), subset=[HA, HB])
        self.assertTrue(subset.get("subset"))
        self.assertIn(carry_state.NV_BAND,
                      [r["band"] for r in subset["rows"]])

    def test_behavior_already_drops_nv(self):
        """K2: the bulk-fix behavior leaves the NV rows out on both cards."""
        self.assertEqual(excluded_by_behavior(doc_of(nv_card_state()),
                                              "fix-loop"), [3, 4])
        self.assertEqual(excluded_by_behavior(finalize_doc(nv_card_state()),
                                              "finalize"), [3, 4])


class TestK2Reproduction(unittest.TestCase):
    def test_k2_rows_doc_has_no_scope_text(self):
        """K2 today: the behavior drops NV rows, the doc cannot say so."""
        for mode, doc in (("fix-loop", doc_of(nv_card_state())),
                          ("finalize", finalize_doc(nv_card_state()))):
            with self.subTest(mode=mode):
                self.assertEqual(excluded_by_behavior(doc, mode), [3, 4])
                self.assertNotIn("bulk_fix_text", doc)
                self.assertNotIn("nv_rows", doc)


class TestScopeTextEqualsBehavior(unittest.TestCase):
    def test_rows_doc_carries_scope_keys(self):
        for mode, doc in (("fix-loop", doc_of(nv_card_state())),
                          ("finalize", finalize_doc(nv_card_state()))):
            with self.subTest(mode=mode):
                self.assertIn("bulk_fix_text", doc)
                self.assertIn("nv_rows", doc)

    def test_fix_loop_equality(self):
        doc = doc_of(nv_card_state())
        self.assertEqual(named_in_text(doc), [3, 4])
        self.assertEqual(doc["nv_rows"], [3, 4])
        self.assertEqual(nv_by_band(doc), [3, 4])
        self.assertEqual(excluded_by_behavior(doc, "fix-loop"), [3, 4])
        self.assertTrue(lock_holds(doc, "fix-loop"))

    def test_finalize_equality(self):
        doc = finalize_doc(nv_card_state())
        self.assertEqual(named_in_text(doc), [3, 4])
        self.assertEqual(doc["nv_rows"], [3, 4])
        self.assertEqual(excluded_by_behavior(doc, "finalize"), [3, 4])
        self.assertTrue(lock_holds(doc, "finalize"))

    def test_exact_text_two_nv_rows(self):
        self.assertEqual(doc_of(nv_card_state())["bulk_fix_text"],
                         FIX_LOOP_TEXT_TWO)
        self.assertEqual(finalize_doc(nv_card_state())["bulk_fix_text"],
                         FINALIZE_TEXT_TWO)

    def test_exact_text_one_nv_row(self):
        for mode, doc, text in (
                ("fix-loop", doc_of(one_nv_state()), FIX_LOOP_TEXT_ONE),
                ("finalize", finalize_doc(one_nv_state()), FINALIZE_TEXT_ONE)):
            with self.subTest(mode=mode):
                self.assertEqual(doc["bulk_fix_text"], text)
                self.assertEqual(doc["nv_rows"], [2])
                self.assertTrue(lock_holds(doc, mode))

    def test_mode_prefixes(self):
        for state in (nv_card_state(), one_nv_state(), no_nv_state()):
            fl = doc_of(state)["bulk_fix_text"]
            fin = finalize_doc(state)["bulk_fix_text"]
            self.assertTrue(fl.startswith(FIX_LOOP_TEXT_PREFIX), fl)
            self.assertTrue(fin.startswith(FINALIZE_TEXT_PREFIX), fin)
        self.assertIn("Other", doc_of(nv_card_state())["bulk_fix_text"])
        self.assertIn("Mixed…", finalize_doc(nv_card_state())["bulk_fix_text"])

    def test_no_nv_card_omits_clause(self):
        for mode, doc, text in (
                ("fix-loop", doc_of(no_nv_state()), FIX_LOOP_TEXT_NONE),
                ("finalize", finalize_doc(no_nv_state()), FINALIZE_TEXT_NONE)):
            with self.subTest(mode=mode):
                self.assertEqual(doc["nv_rows"], [])
                self.assertEqual(doc["bulk_fix_text"], text)
                self.assertNotIn("Needs-verification", doc["bulk_fix_text"])
                self.assertNotIn("#", doc["bulk_fix_text"])
                self.assertEqual(excluded_by_behavior(doc, mode), [])
                self.assertTrue(lock_holds(doc, mode))

    def test_subset_card_excludes_nothing(self):
        doc = doc_of(nv_card_state(), subset=[HA, HB])
        self.assertEqual(doc["nv_rows"], [])
        self.assertNotIn("Needs-verification", doc["bulk_fix_text"])
        self.assertEqual(doc["bulk_fix_text"], FIX_LOOP_TEXT_NONE)
        chosen, reason = batch_card.select(doc["rows"], {"all": True},
                                           subset=True)
        self.assertIsNone(reason)
        self.assertEqual(chosen["rows"], [r["n"] for r in doc["rows"]])
        self.assertTrue(lock_holds(doc, "fix-loop"))

    def test_text_is_numbers_and_literals_only(self):
        """T-58-01: diff-authored titles/paths never reach the description."""
        state = nv_card_state()
        for mode, doc in (("fix-loop", doc_of(state)),
                          ("finalize", finalize_doc(state))):
            with self.subTest(mode=mode):
                text = doc["bulk_fix_text"]
                self.assertRegex(text, r"^[^\n]*$")
                for row in doc["rows"]:
                    self.assertNotIn(row["title"], text)
                    self.assertNotIn(row["file"], text)


class TestScopeLockTrips(unittest.TestCase):
    """Each named mutant makes the text/behavior lock fail."""

    def test_m1_fix_rest_reaches_nv(self):
        real_doc = finalize_doc(nv_card_state())
        real = excluded_by_behavior(real_doc, "finalize")
        widened = ("critical", "warning", carry_state.NV_BAND, "medium")
        with mock.patch.object(
                batch_parse, "_rest_bands_for",
                lambda verb: widened if verb == "fix" else ("medium",)):
            doc = finalize_doc(nv_card_state())
            mutated = excluded_by_behavior(doc, "finalize")
            held = lock_holds(doc, "finalize")
        with self.subTest("mutant: _rest_bands_for('fix') includes NV"):
            self.assertNotEqual(mutated, real)
            self.assertFalse(held)

    def test_m2_select_keeps_nv(self):
        real_doc = doc_of(nv_card_state())
        real = excluded_by_behavior(real_doc, "fix-loop")
        real_select = batch_card.select
        with mock.patch.object(
                batch_card, "select",
                lambda rows, answer, subset=False:
                real_select(rows, answer, subset=True)):
            doc = doc_of(nv_card_state())
            mutated = excluded_by_behavior(doc, "fix-loop")
            held = lock_holds(doc, "fix-loop")
        with self.subTest("mutant: select(all) keeps NV rows"):
            self.assertNotEqual(mutated, real)
            self.assertFalse(held)

    def test_m3_number_dropped_from_text(self):
        real_texts = batch_card.option_texts

        def drop_last(rows, mode, subset):
            out = dict(real_texts(rows, mode, subset))
            out["bulk_fix_text"] = out["bulk_fix_text"].replace(", #4", "")
            return out

        for mode, build in (("fix-loop", doc_of), ("finalize", finalize_doc)):
            real = build(nv_card_state())
            with mock.patch.object(batch_card, "option_texts", drop_last):
                doc = build(nv_card_state())
            with self.subTest("mutant: a number dropped from the text",
                              mode=mode):
                self.assertNotEqual(doc["bulk_fix_text"],
                                    real["bulk_fix_text"])
                self.assertFalse(lock_holds(doc, mode))

    def test_m4_subset_names_rows(self):
        real_texts = batch_card.option_texts

        def subset_nv(rows, mode, subset):
            out = dict(real_texts(rows, mode, subset))
            if subset:
                out["nv_rows"] = [1]
            return out

        real = doc_of(nv_card_state(), subset=[HA, HB])
        with mock.patch.object(batch_card, "option_texts", subset_nv):
            doc = doc_of(nv_card_state(), subset=[HA, HB])
        with self.subTest("mutant: non-empty nv_rows on a subset card"):
            self.assertNotEqual(doc["nv_rows"], real["nv_rows"])
            self.assertFalse(lock_holds(doc, "fix-loop"))


if __name__ == "__main__":
    unittest.main()
