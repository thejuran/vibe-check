"""test_answer_resolve.py — plain-English card answers resolved to grammar.

`batch_card.py resolve` maps the owner's references (current row numbers,
numbers from an older card, title words, card markers, and the counted
complement "the N <desc> rows") to current rows and builds a grammar string
that the unchanged strict `parse` then validates. The parser stays the only
gate: resolve decides nothing, it only says which rows each reference names
and whether every reference is clear.

Owner text reaches resolve only through the refs file. Finding titles are
diff data and are matched as data (case-folded word containment over the
one-line title), never read as instructions. Every refusal is one fixed
line from REASONS.
"""

import copy
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module under test)
import batch_parse  # noqa: E402
import carry_state  # noqa: E402
from test_batch_card import (  # noqa: E402
    ALL_REASONS, TempDirCase, run_cli, synth_rows)

HERE = os.path.dirname(os.path.abspath(__file__))
SIX_ROW_FIXTURE = os.path.join(HERE, "fixtures",
                               "iplayarr45-six-row-state.json")

NEW_REASON_NAMES = ("REASON_REFS", "REASON_PRIOR_ROWS", "REASON_PRIOR_NEEDED")
RESOLVE_REASONS = set(ALL_REASONS) | {
    getattr(batch_card, name) for name in NEW_REASON_NAMES
    if hasattr(batch_card, name)}

BROWSE_TITLE = "Browse recovery leaves a stale cursor after a failed page load"
BROWSE_HASH = "ab" * 32
SYNTH_WARNING_TITLE = "Retry budget is not reset after a successful relay"
SYNTH_WARNING_HASH = "cd" * 32
OWNER_REASON = 'fixed (owner: "dismiss the 7 fixed rows")'
V1_PLAIN = ("fix the Browse recovery issue, then dismiss the 7 fixed rows "
            "and close out")
V1_REASON = "fixed in review-pass commits, verified on recheck"
V1_GRAMMAR = "fix 5; dismiss 1,2,3,4,6,7,8 -- " + V1_REASON
ROW_KEYS = ("stable_hash", "band", "file", "line", "title", "pending_since",
            "stale", "absorbed_into")


def _real_six_rows():
    with open(SIX_ROW_FIXTURE, encoding="utf-8") as fh:
        state = json.load(fh)
    doc, reason = batch_card.build_rows(state, "fix-loop", None, None)
    assert reason is None, reason
    return doc["rows"]


def _renumber(rows):
    return [dict(row, n=i + 1) for i, row in enumerate(rows)]


def _retitled(rows_doc, n, title):
    """A deep copy of `rows_doc` with row n's title replaced."""
    doc = copy.deepcopy(rows_doc)
    doc["rows"][n - 1]["title"] = title
    return doc


def _rebanded(rows_doc, n, band):
    """A deep copy of `rows_doc` with row n's band replaced."""
    doc = copy.deepcopy(rows_doc)
    doc["rows"][n - 1]["band"] = band
    return doc


def iplayarr_rows(at_pass=3):
    """The eight-row fix-loop card behind the repeated-card loop: the six real
    iPlayarr rows (3 critical, 2 warning, 1 medium) plus one synthetic
    warning, with the Browse recovery warning as row 5."""
    real = [{k: row[k] for k in ROW_KEYS} for row in _real_six_rows()]
    browse = {"stable_hash": BROWSE_HASH, "band": "warning",
              "file": "src/browse/recovery.ts", "line": 118,
              "title": BROWSE_TITLE, "pending_since": None, "stale": None,
              "absorbed_into": None}
    synth = {"stable_hash": SYNTH_WARNING_HASH, "band": "warning",
             "file": "src/relay/budget.ts", "line": 33,
             "title": SYNTH_WARNING_TITLE, "pending_since": 2, "stale": None,
             "absorbed_into": None}
    rows = real[0:4] + [browse, real[4], synth, real[5]]
    return {"at_pass": at_pass, "mode": "fix-loop", "rows": _renumber(rows)}


def timeout_rows():
    """Four rows where two titles contain "timeout" (rows 2 and 4)."""
    doc = synth_rows(4)
    doc["rows"][1]["title"] = "Request timeout is not retried"
    doc["rows"][3]["title"] = "Socket timeout leaks a handle"
    return doc


def pending_rows():
    """Three rows; only row 2 is pending since an earlier pass."""
    doc = synth_rows(3)
    for row in doc["rows"]:
        row["pending_since"] = None
    doc["rows"][1]["pending_since"] = 1
    return doc


def stale_pair():
    """(prior doc at pass 3, current doc at pass 4).

    Current card: prior rows 1 and 2 are gone (fixed), so every later row
    moved up two places; prior row 6 was re-hashed by an edit (same file and
    title); prior row 7 kept its hash but its title was reworded."""
    prior = iplayarr_rows(at_pass=3)
    rows = copy.deepcopy(prior["rows"][2:])
    rows[3]["stable_hash"] = "ee" * 32            # prior row 6
    rows[4]["title"] = "Relay retry budget never resets"  # prior row 7
    current = {"at_pass": 4, "mode": "fix-loop", "rows": _renumber(rows)}
    return prior, current


def ref_number(verb, n):
    return {"verb": verb, "kind": "number", "n": n}


def ref_prior(verb, n):
    return {"verb": verb, "kind": "prior_number", "n": n}


def ref_title(verb, text):
    return {"verb": verb, "kind": "title", "text": text}


def ref_marker(verb, marker, count=None):
    ref = {"verb": verb, "kind": "marker", "marker": marker}
    if count is not None:
        ref["count"] = count
    return ref


def refs_doc(refs, reason=None, close_out=False):
    return {"refs": refs, "reason": reason, "close_out": close_out}


def eight_row_refs(count=7, reason=OWNER_REASON):
    return refs_doc([ref_title("fix", "Browse recovery"),
                     ref_marker("dismiss", "remaining", count)],
                    reason=reason, close_out=True)


def resolve(rows_doc, refs, prior=None):
    out, reason = batch_card.resolve_refs(rows_doc, refs, prior)
    assert reason is None, reason
    return out


def parse_rows(rows_doc, grammar):
    """{verb: [row numbers]} the unchanged parser acts on for `grammar`."""
    parsed, reason = batch_card.parse(rows_doc, {"q1": grammar, "q2": None})
    assert reason is None, reason
    n_of = {r["stable_hash"]: r["n"] for r in rows_doc["rows"]}
    return {verb: sorted(n_of[h] for h in parsed[verb])
            for verb in batch_parse.VERBS}


# Lock checks shared by the real tests and their mutants. Each raises
# AssertionError when the guarded behavior is broken.
def check_count_mismatch(tc, out):
    tc.assertEqual(out["refs"][1]["status"], "count_mismatch")
    tc.assertIsNone(out["grammar"])
    tc.assertFalse(out["ok"])


def check_ambiguous_title(tc, out):
    tc.assertEqual(out["refs"][0]["status"], "many")
    tc.assertEqual(out["refs"][0]["rows"], [])
    tc.assertEqual([c["label"] for c in out["refs"][0]["candidates"]],
                   ["#2 app/f1.py:2", "#4 app/f3.py:4"])
    tc.assertIsNone(out["grammar"])
    tc.assertFalse(out["ok"])


def check_no_broadening(tc, rows_doc, out):
    """The rows the parser acts on equal, verb by verb, the rows resolve
    says the owner named (D-04)."""
    tc.assertTrue(out["ok"])
    tc.assertEqual(parse_rows(rows_doc, out["grammar"]),
                   {verb: out["verbs"][verb] for verb in batch_parse.VERBS})


def check_hash_remap(tc, out, new_n):
    tc.assertEqual(out["refs"][0]["status"], "one")
    tc.assertEqual(out["refs"][0]["rows"], [new_n])


def check_conflict(tc, out):
    tc.assertEqual(out["refs"][1]["status"], "conflict")
    tc.assertFalse(out["ok"])
    tc.assertIsNone(out["grammar"])


# --------------------------------------------------------------------------- #
# The fixtures contain what the tests say they contain.
# --------------------------------------------------------------------------- #
class TestFixture(unittest.TestCase):
    def test_eight_rows_with_browse_as_row_5(self):
        doc = iplayarr_rows()
        rows = doc["rows"]
        self.assertEqual(len(rows), 8)
        self.assertEqual([r["n"] for r in rows], list(range(1, 9)))
        self.assertIn("Browse", rows[4]["title"])
        others = [r["title"] for i, r in enumerate(rows) if i != 4]
        self.assertFalse(any("browse" in t.casefold() for t in others))
        self.assertEqual([r["band"] for r in rows],
                         ["critical"] * 3 + ["warning"] * 4 + ["medium"])
        self.assertEqual(len({r["stable_hash"] for r in rows}), 8)
        self.assertTrue(batch_card._valid_rows_doc(doc))

    def test_real_six_rows_are_three_two_one(self):
        bands = [r["band"] for r in _real_six_rows()]
        self.assertEqual(bands, ["critical"] * 3 + ["warning"] * 2
                         + ["medium"])

    def test_timeout_and_pending_fixtures(self):
        titles = [r["title"] for r in timeout_rows()["rows"]]
        self.assertEqual([i + 1 for i, t in enumerate(titles)
                          if "timeout" in t.casefold()], [2, 4])
        self.assertEqual([r["n"] for r in pending_rows()["rows"]
                          if r["pending_since"] is not None], [2])

    def test_stale_pair_shape(self):
        prior, current = stale_pair()
        p, c = prior["rows"], current["rows"]
        self.assertEqual(len(c), 6)
        self.assertEqual(c[2]["stable_hash"], p[4]["stable_hash"])  # Browse
        self.assertNotIn(p[0]["stable_hash"], [r["stable_hash"] for r in c])
        self.assertNotIn(p[5]["stable_hash"], [r["stable_hash"] for r in c])
        self.assertEqual((c[3]["file"], c[3]["title"]),
                         (p[5]["file"], p[5]["title"]))
        self.assertEqual(c[4]["stable_hash"], p[6]["stable_hash"])
        self.assertNotEqual(c[4]["title"], p[6]["title"])


# --------------------------------------------------------------------------- #
# V1: the plain-English answer is refused today; the grammar form is accepted.
# --------------------------------------------------------------------------- #
class TestV1Reproduction(TempDirCase):
    def _parse(self, q1):
        rows = self.write("rows.json", iplayarr_rows())
        return run_cli(["parse", "--rows", rows, "--answer",
                        self.write("ans.json", {"q1": q1, "q2": None})])

    def test_plain_english_answer_refused(self):
        proc = self._parse(V1_PLAIN)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr.decode(), batch_parse.REASON_TOKEN)

    def test_grammar_answer_accepted(self):
        rows = iplayarr_rows()["rows"]
        proc = self._parse(V1_GRAMMAR)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout)
        self.assertEqual(out["fix_targets"], [rows[4]["stable_hash"]])
        decisions = out["payload"]["decisions"]
        self.assertEqual(len(decisions), 7)
        self.assertEqual({d["decision"] for d in decisions}, {"dismiss"})
        self.assertEqual({d["reason"] for d in decisions}, {V1_REASON})
        self.assertEqual([d["stable_hash"] for d in decisions],
                         [rows[i]["stable_hash"] for i in (0, 1, 2, 3, 5, 6,
                                                           7)])


# --------------------------------------------------------------------------- #
# The eight-row case resolves and the parser accepts it (ANSR-01).
# --------------------------------------------------------------------------- #
class TestResolveEightRow(unittest.TestCase):
    def test_eight_row_grammar(self):
        out = resolve(iplayarr_rows(), eight_row_refs())
        self.assertTrue(out["ok"])
        self.assertEqual(out["grammar"],
                         "fix 5; dismiss 1,2,3,4,6,7,8 -- " + OWNER_REASON)
        self.assertEqual(out["verbs"], {"fix": [5],
                                        "dismiss": [1, 2, 3, 4, 6, 7, 8],
                                        "defer": []})
        self.assertEqual([r["status"] for r in out["refs"]], ["one", "one"])
        self.assertEqual(out["refs"][0]["rows"], [5])
        self.assertTrue(out["close_out"])
        self.assertFalse(out["stale"])
        self.assertFalse(out["needs_reason"])
        self.assertIsNone(out["parse_reason"])

    def test_same_gate_as_the_v1_grammar(self):
        doc = iplayarr_rows()
        out = resolve(doc, eight_row_refs())
        ours, r1 = batch_card.parse(doc, {"q1": out["grammar"], "q2": None})
        theirs, r2 = batch_card.parse(doc, {"q1": V1_GRAMMAR, "q2": None})
        self.assertIsNone(r1)
        self.assertIsNone(r2)
        self.assertEqual(ours["fix_targets"], theirs["fix_targets"])
        self.assertEqual(
            [(d["stable_hash"], d["decision"])
             for d in ours["payload"]["decisions"]],
            [(d["stable_hash"], d["decision"])
             for d in theirs["payload"]["decisions"]])
        self.assertEqual({d["reason"] for d in ours["payload"]["decisions"]},
                         {OWNER_REASON})

    def test_close_out_echoed_unchanged(self):
        refs = eight_row_refs()
        refs["close_out"] = False
        self.assertFalse(resolve(iplayarr_rows(), refs)["close_out"])

    def test_eight_row_no_broadening(self):
        doc = iplayarr_rows()
        check_no_broadening(self, doc, resolve(doc, eight_row_refs()))


# --------------------------------------------------------------------------- #
# Gaps: count mismatch, ambiguity, gone rows, markers, reason, conflict, bulk.
# --------------------------------------------------------------------------- #
class TestResolveGaps(unittest.TestCase):
    def test_count_mismatch_asks(self):
        out = resolve(iplayarr_rows(), eight_row_refs(count=6))
        check_count_mismatch(self, out)
        self.assertEqual(out["refs"][0]["status"], "one")

    def test_count_mismatch_lists_matched_rows(self):
        out = resolve(iplayarr_rows(), eight_row_refs(count=6))
        self.assertEqual([c["label"].split()[0]
                          for c in out["refs"][1]["candidates"]],
                         ["#1", "#2", "#3", "#4", "#6", "#7", "#8"])

    def test_ambiguous_title_many(self):
        out = resolve(timeout_rows(),
                      refs_doc([ref_title("fix", "timeout")]))
        check_ambiguous_title(self, out)
        for cand in out["refs"][0]["candidates"]:
            self.assertLessEqual(len(cand["title"]), 80)

    def test_title_none(self):
        out = resolve(iplayarr_rows(),
                      refs_doc([ref_title("fix", "nonexistent zebra")]))
        self.assertEqual(out["refs"][0]["status"], "none")
        self.assertEqual(out["refs"][0]["rows"], [])
        self.assertIsNone(out["grammar"])
        self.assertFalse(out["ok"])

    def test_title_words_in_any_order_case_folded(self):
        out = resolve(iplayarr_rows(),
                      refs_doc([ref_title("fix", "RECOVERY browse")]))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [5])

    def test_number_out_of_range_is_none(self):
        out = resolve(iplayarr_rows(), refs_doc([ref_number("fix", 9)]))
        self.assertEqual(out["refs"][0]["status"], "none")
        self.assertFalse(out["ok"])

    def test_band_medium_without_count(self):
        doc = iplayarr_rows()
        out = resolve(doc, refs_doc([ref_marker("fix", "band:medium")]))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [8])
        self.assertEqual(out["grammar"], "fix 8")
        check_no_broadening(self, doc, out)

    def test_band_critical_count_matches(self):
        doc = iplayarr_rows()
        out = resolve(doc, refs_doc(
            [ref_marker("dismiss", "band:critical", 3)], reason="Out of scope"))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["grammar"], "dismiss 1,2,3 -- Out of scope")
        check_no_broadening(self, doc, out)

    def test_band_critical_count_mismatch(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_marker("dismiss", "band:critical", 2)], reason="x"))
        self.assertEqual(out["refs"][0]["status"], "count_mismatch")
        self.assertIsNone(out["grammar"])

    def test_band_with_no_rows_is_none(self):
        out = resolve(iplayarr_rows(),
                      refs_doc([ref_marker("fix", "band:needs-verification")]))
        self.assertEqual(out["refs"][0]["status"], "none")

    def test_pending_marker(self):
        out = resolve(pending_rows(), refs_doc([ref_marker("fix", "pending")]))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [2])

    def test_changed_and_absorbed_markers(self):
        doc = synth_rows(3)
        for row in doc["rows"]:
            row.update(stale=None, absorbed_into=None)
        doc["rows"][0]["stale"] = {"cause": "code", "decision": "dismiss"}
        doc["rows"][2]["absorbed_into"] = "%064x" % 1
        changed = resolve(doc, refs_doc([ref_marker("fix", "changed")]))
        absorbed = resolve(doc, refs_doc([ref_marker("fix", "absorbed")]))
        self.assertEqual(changed["refs"][0]["rows"], [1])
        self.assertEqual(absorbed["refs"][0]["rows"], [3])

    def test_missing_reason_needs_reason(self):
        out = resolve(iplayarr_rows(), refs_doc([ref_number("dismiss", 3)]))
        self.assertEqual(out["grammar"], "dismiss 3")
        self.assertTrue(out["needs_reason"])
        self.assertEqual(out["parse_reason"], batch_parse.REASON_NO_REASON)
        self.assertFalse(out["ok"])

    def test_empty_reason_counts_as_none(self):
        out = resolve(iplayarr_rows(),
                      refs_doc([ref_number("defer", 3)], reason="  "))
        self.assertEqual(out["grammar"], "defer 3")
        self.assertTrue(out["needs_reason"])

    def test_conflict(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_number("fix", 5), ref_number("dismiss", 5)], reason="x"))
        check_conflict(self, out)
        self.assertEqual(out["refs"][0]["status"], "one")

    def test_remaining_blocked_by_unclear_ref(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_title("fix", "zebra"), ref_marker("dismiss", "remaining", 7)],
            reason="x"))
        self.assertEqual([r["status"] for r in out["refs"]],
                         ["none", "blocked"])
        self.assertIsNone(out["grammar"])

    def test_bulk_remaining_without_count_is_rest(self):
        doc = iplayarr_rows()
        out = resolve(doc, refs_doc(
            [ref_title("fix", "Browse recovery"),
             ref_marker("dismiss", "remaining")], reason="fixed"))
        self.assertEqual(out["refs"][1]["status"], "bulk")
        self.assertEqual(out["grammar"], "fix 5; dismiss rest -- fixed")
        dismissed = parse_rows(doc, out["grammar"])["dismiss"]
        mediums = [r["n"] for r in doc["rows"] if r["band"] == "medium"]
        self.assertTrue(set(dismissed) <= set(mediums))
        self.assertEqual(dismissed, [8])
        check_no_broadening(self, doc, out)

    def test_counted_reference_never_emits_rest_or_all(self):
        out = resolve(iplayarr_rows(), eight_row_refs())
        clauses = out["grammar"].split(" -- ")[0]
        self.assertNotIn("rest", clauses)
        self.assertNotIn("all", clauses)

    def test_clause_order_fix_dismiss_defer(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_number("defer", 2), ref_number("dismiss", 7),
             ref_number("fix", 4), ref_number("dismiss", 1)], reason="r"))
        self.assertEqual(out["grammar"], "fix 4; dismiss 1,7; defer 2 -- r")


# --------------------------------------------------------------------------- #
# Gap round: whole-token titles (WR-03), `changed` excludes joined (IN-03),
# serious described groups need a count (D-18), two uncounted `remaining`
# references are a parser refusal with every reference clear (WR-04).
# --------------------------------------------------------------------------- #
VERBATIM_TITLE_CLAUSE = "the Browse recovery issue"


def fragment_rows():
    doc = _retitled(iplayarr_rows(), 2, "Unused import of os")
    return _retitled(doc, 3, "Pagination off by one")


def stale_cause_rows():
    """The eight-row card with row 1 changed by code, row 2 joined, row 3
    changed nearby and row 4 changed by severity (rows 1-3 are critical)."""
    doc = copy.deepcopy(iplayarr_rows())
    for n, cause in ((1, "code"), (2, "joined"), (3, "nearby"),
                     (4, "severity")):
        doc["rows"][n - 1]["stale"] = {"cause": cause, "decision": "dismiss"}
    return doc


def title_status(rows_doc, text):
    ref = resolve(rows_doc, refs_doc([ref_title("fix", text)]))["refs"][0]
    return ref["status"], ref["rows"]


def check_verbatim_clause(tc, out):
    tc.assertTrue(out["ok"])
    tc.assertEqual(out["refs"][0]["status"], "one")
    tc.assertEqual(out["refs"][0]["rows"], [5])
    tc.assertEqual(out["grammar"],
                   "fix 5; dismiss 1,2,3,4,6,7,8 -- " + OWNER_REASON)


def check_fragments_none(tc):
    doc = fragment_rows()
    tc.assertEqual(title_status(doc, "port"), ("none", []))
    tc.assertEqual(title_status(doc, "on"), ("none", []))


def check_changed_excludes_joined(tc, out):
    tc.assertEqual(out["refs"][0]["status"], "one")
    tc.assertEqual(out["refs"][0]["rows"], [1, 3, 4])


def check_count_needed(tc, out, labels):
    ref = out["refs"][0]
    tc.assertEqual(ref["status"], "count_needed")
    tc.assertEqual(ref["rows"], [])
    tc.assertEqual([c["label"].split()[0] for c in ref["candidates"]], labels)
    tc.assertFalse(out["ok"])
    tc.assertFalse(out["needs_reason"])
    tc.assertIsNone(out["grammar"])


def verbatim_refs():
    return refs_doc([ref_title("fix", VERBATIM_TITLE_CLAUSE),
                     ref_marker("dismiss", "remaining", 7)],
                    reason=OWNER_REASON, close_out=True)


def nv_dismiss_case():
    doc = _rebanded(iplayarr_rows(), 6, carry_state.NV_BAND)
    return doc, refs_doc([ref_marker("dismiss",
                                     "band:" + carry_state.NV_BAND)])


class TestGapRound(unittest.TestCase):
    def test_v1_verbatim_title_clause_resolves(self):
        self.assertIn(VERBATIM_TITLE_CLAUSE, V1_PLAIN)
        self.assertIn("the 7 fixed rows", V1_PLAIN)
        out = resolve(iplayarr_rows(), verbatim_refs())
        check_verbatim_clause(self, out)
        self.assertTrue(out["close_out"])
        self.assertFalse(out["needs_reason"])

    def test_filler_words_do_not_block_match(self):
        for text in ("the Browse recovery bug", "that browse recovery one"):
            with self.subTest(text):
                self.assertEqual(title_status(iplayarr_rows(), text),
                                 ("one", [5]))

    def test_fragment_inside_a_word_is_none(self):
        doc = fragment_rows()
        check_fragments_none(self)
        self.assertEqual(title_status(doc, "import"), ("one", [2]))
        self.assertEqual(title_status(doc, "off by one"), ("one", [3]))

    def test_filler_only_text_is_none(self):
        # "a" is inside every title as a letter and as a word: filler-only
        # text names no row, never one or many.
        for text in ("the issue", "a", "this one"):
            with self.subTest(text):
                out = resolve(iplayarr_rows(),
                              refs_doc([ref_title("fix", text)]))
                ref = out["refs"][0]
                self.assertEqual(ref["status"], "none")
                self.assertEqual(ref["candidates"], [])
                self.assertFalse(out["ok"])

    def test_title_tokens_are_punctuation_insensitive(self):
        for text in ("browse-recovery", "Browse, recovery."):
            with self.subTest(text):
                self.assertEqual(title_status(iplayarr_rows(), text),
                                 ("one", [5]))

    def test_changed_marker_excludes_joined(self):
        out = resolve(stale_cause_rows(),
                      refs_doc([ref_marker("fix", "changed")]))
        check_changed_excludes_joined(self, out)

    def test_dismiss_serious_group_without_count_needs_count(self):
        doc, refs = nv_dismiss_case()
        check_count_needed(self, resolve(doc, refs), ["#6"])
        with self.subTest("defer band:warning"):
            out = resolve(iplayarr_rows(), refs_doc(
                [ref_marker("defer", "band:warning")], reason="later"))
            check_count_needed(self, out, ["#4", "#5", "#6", "#7"])
        with self.subTest("dismiss changed incl. a critical"):
            out = resolve(stale_cause_rows(), refs_doc(
                [ref_marker("dismiss", "changed")], reason="x"))
            check_count_needed(self, out, ["#1", "#3", "#4"])

    def test_medium_and_fix_groups_without_count_still_one(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_marker("dismiss", "band:medium")], reason="noise"))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [8])
        self.assertTrue(out["ok"])
        out = resolve(iplayarr_rows(),
                      refs_doc([ref_marker("fix", "band:critical")]))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [1, 2, 3])

    def test_counted_serious_group_matches(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_marker("dismiss", "band:critical", 3)], reason="x"))
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [1, 2, 3])
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_marker("dismiss", "band:critical", 2)], reason="x"))
        self.assertEqual(out["refs"][0]["status"], "count_mismatch")

    def test_two_uncounted_remaining_is_ok_false_with_every_ref_clear(self):
        out = resolve(iplayarr_rows(), refs_doc(
            [ref_number("fix", 1), ref_marker("dismiss", "remaining"),
             ref_marker("defer", "remaining")], reason="x"))
        self.assertFalse(out["ok"])
        self.assertTrue(all(r["status"] in ("one", "bulk")
                            for r in out["refs"]))
        self.assertFalse(out["needs_reason"])
        self.assertEqual(out["parse_reason"], batch_parse.REASON_REST_TWICE)


class TestGapRoundLockTrips(unittest.TestCase):
    """Each gap-round guard is load-bearing: its mutant trips the lock."""

    def test_m6_substring_matching_restored(self):
        def substring_match(rows, text):
            words = text.casefold().split()
            return [r for r in rows if all(
                w in batch_card._one_line(r.get("title")).casefold()
                for w in words)]

        with self.subTest("real"):
            check_fragments_none(self)
        with self.subTest("mutant: substring title match"):
            with mock.patch.object(batch_card, "_match_title",
                                   substring_match):
                self.assertNotEqual(title_status(fragment_rows(), "port"),
                                    ("none", []))
                with self.assertRaises(AssertionError):
                    check_fragments_none(self)

    def test_m7_filler_not_stripped(self):
        doc, refs = iplayarr_rows(), verbatim_refs()
        with self.subTest("real"):
            check_verbatim_clause(self, resolve(doc, refs))
        with self.subTest("mutant: filler kept"):
            with mock.patch.object(batch_card, "_TITLE_FILLER", frozenset()):
                out = resolve(doc, refs)
            self.assertEqual(out["refs"][0]["status"], "none")
            with self.assertRaises(AssertionError):
                check_verbatim_clause(self, out)

    def test_m8_changed_includes_joined(self):
        doc = stale_cause_rows()
        refs = refs_doc([ref_marker("fix", "changed")])
        real_marker_rows = batch_card._marker_rows

        def any_stale(rows, marker):
            if marker == "changed":
                return [r for r in rows if r.get("stale")]
            return real_marker_rows(rows, marker)

        with self.subTest("real"):
            check_changed_excludes_joined(self, resolve(doc, refs))
        with self.subTest("mutant: changed includes joined"):
            with mock.patch.object(batch_card, "_marker_rows", any_stale):
                out = resolve(doc, refs)
            self.assertIn(2, out["refs"][0]["rows"])
            with self.assertRaises(AssertionError):
                check_changed_excludes_joined(self, out)

    def test_m9_serious_group_without_count_acts(self):
        doc, refs = nv_dismiss_case()
        with self.subTest("real"):
            check_count_needed(self, resolve(doc, refs), ["#6"])
        with self.subTest("mutant: D-18 check removed"):
            with mock.patch.object(batch_card, "_needs_count",
                                   lambda ref, matched: False):
                out = resolve(doc, refs)
            self.assertEqual(out["refs"][0]["status"], "one")
            self.assertEqual(out["refs"][0]["rows"], [6])
            with self.assertRaises(AssertionError):
                check_count_needed(self, out, ["#6"])


# --------------------------------------------------------------------------- #
# Stale card: prior numbers re-mapped by finding identity (D-07).
# --------------------------------------------------------------------------- #
class TestResolveStale(unittest.TestCase):
    def test_prior_number_remapped_by_hash(self):
        prior, current = stale_pair()
        out = resolve(current, refs_doc([ref_prior("fix", 5)]), prior)
        check_hash_remap(self, out, 3)
        self.assertTrue(out["stale"])
        self.assertEqual(out["grammar"], "fix 3")

    def test_rehashed_row_remapped_by_file_title(self):
        prior, current = stale_pair()
        out = resolve(current, refs_doc([ref_prior("fix", 6)]), prior)
        self.assertEqual(out["refs"][0]["status"], "one")
        self.assertEqual(out["refs"][0]["rows"], [4])

    def test_retitled_row_keeps_hash_identity(self):
        prior, current = stale_pair()
        out = resolve(current, refs_doc([ref_prior("fix", 7)]), prior)
        check_hash_remap(self, out, 5)

    def test_gone_row_is_none(self):
        prior, current = stale_pair()
        out = resolve(current, refs_doc([ref_prior("fix", 1)]), prior)
        self.assertEqual(out["refs"][0]["status"], "none")
        self.assertFalse(out["ok"])

    def test_prior_number_out_of_range_is_none(self):
        prior, current = stale_pair()
        out = resolve(current, refs_doc([ref_prior("fix", 9)]), prior)
        self.assertEqual(out["refs"][0]["status"], "none")

    def test_two_file_title_candidates_is_many(self):
        prior, current = stale_pair()
        twin = dict(current["rows"][3], stable_hash="ff" * 32)
        current["rows"].append(twin)
        current["rows"] = _renumber(current["rows"])
        out = resolve(current, refs_doc([ref_prior("fix", 6)]), prior)
        self.assertEqual(out["refs"][0]["status"], "many")
        self.assertEqual(len(out["refs"][0]["candidates"]), 2)

    def test_same_card_is_not_stale(self):
        doc = iplayarr_rows()
        out = resolve(doc, refs_doc([ref_prior("fix", 5)]), copy.deepcopy(doc))
        self.assertFalse(out["stale"])
        self.assertEqual(out["refs"][0]["rows"], [5])

    def test_new_pass_same_rows_is_stale(self):
        doc = iplayarr_rows(at_pass=4)
        out = resolve(doc, refs_doc([ref_number("fix", 5)]),
                      iplayarr_rows(at_pass=3))
        self.assertTrue(out["stale"])

    def test_prior_number_without_prior_rows_refused(self):
        out, reason = batch_card.resolve_refs(
            iplayarr_rows(), refs_doc([ref_prior("fix", 5)]), None)
        self.assertIsNone(out)
        self.assertEqual(reason, batch_card.REASON_PRIOR_NEEDED)


# --------------------------------------------------------------------------- #
# CLI: refusals are fixed strings, owner text never leaks, tables sealed.
# --------------------------------------------------------------------------- #
class TestResolveCli(TempDirCase):
    def _resolve(self, refs, rows=None, prior=None, stdin_bytes=b""):
        argv = ["resolve", "--rows",
                self.write("rows.json", rows or iplayarr_rows()),
                "--answer", self.write("refs.json", refs)]
        if prior is not None:
            argv += ["--prior-rows", self.write("prior.json", prior)]
        return run_cli(argv, stdin_bytes=stdin_bytes)

    def test_cli_eight_row(self):
        proc = self._resolve(eight_row_refs())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout)
        self.assertEqual(out["grammar"],
                         "fix 5; dismiss 1,2,3,4,6,7,8 -- " + OWNER_REASON)
        self.assertEqual(out, batch_card.resolve_refs(iplayarr_rows(),
                                                      eight_row_refs())[0])

    def test_cli_count_mismatch_exits_zero(self):
        proc = self._resolve(eight_row_refs(count=6))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout)["refs"][1]["status"],
                         "count_mismatch")

    def test_cli_stale(self):
        prior, current = stale_pair()
        proc = self._resolve(refs_doc([ref_prior("fix", 5)]), rows=current,
                             prior=prior)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout)
        self.assertTrue(out["stale"])
        self.assertEqual(out["refs"][0]["rows"], [3])

    def test_cli_prior_needed(self):
        proc = self._resolve(refs_doc([ref_prior("fix", 5)]))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_PRIOR_NEEDED)

    def test_cli_prior_rows_malformed(self):
        proc = self._resolve(refs_doc([ref_prior("fix", 5)]),
                             prior={"rows": "nope"})
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_PRIOR_ROWS)

    def test_cli_malformed_refs(self):
        good = ref_title("fix", "Browse recovery zebra")
        bad_docs = {
            "missing refs": {"reason": "Browse zebra"},
            "refs not a list": {"refs": "Browse zebra"},
            "empty refs": {"refs": []},
            "unknown top key": dict(refs_doc([good]), extra="Browse zebra"),
            "bad verb": refs_doc([dict(good, verb="Browse zebra")]),
            "bad kind": refs_doc([dict(good, kind="Browse zebra")]),
            "extra ref key": refs_doc([dict(good, n=1)]),
            "empty text": refs_doc([ref_title("fix", "")]),
            "blank text": refs_doc([ref_title("fix", "   ")]),
            "count zero": refs_doc([ref_marker("fix", "remaining", 0)]),
            "count bool": refs_doc([ref_marker("fix", "remaining", True)]),
            "count on title": refs_doc([dict(good, count=2)]),
            "bad marker": refs_doc([ref_marker("fix", "Browse zebra")]),
            "number zero": refs_doc([ref_number("fix", 0)]),
            "number string": refs_doc([ref_number("fix", "5")]),
            "reason not str": refs_doc([good], reason=["Browse zebra"]),
            "close_out not bool": dict(refs_doc([good]), close_out="yes"),
            "not json": "{Browse zebra",
        }
        for name, doc in bad_docs.items():
            with self.subTest(name):
                proc = self._resolve(doc)
                self.assertEqual(proc.returncode, 2, name)
                self.assertEqual(proc.stdout, b"")
                err = proc.stderr.decode()
                self.assertEqual(err, batch_card.REASON_REFS)
                self.assertIn(err, RESOLVE_REASONS)
                self.assertNotIn("Browse", err)
                self.assertNotIn("zebra", err)

    def test_cli_rows_malformed(self):
        proc = self._resolve(eight_row_refs(), rows={"rows": []})
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stderr.decode(), batch_card.REASON_ROWS)

    def test_sealed_tuples(self):
        # The full ordered tuple is pinned in test_batch_card.
        self.assertIn("resolve", batch_card.SUBCOMMANDS)
        self.assertIn("--prior-rows", batch_card.KNOWN_FLAGS)
        self.assertNotIn("resolve", batch_card._STATE_SUBCOMMANDS)
        self.assertEqual(batch_card._FLAGS_BY_SUBCOMMAND["resolve"],
                         (("--rows", "--answer"), ("--prior-rows",)))
        for name in NEW_REASON_NAMES:
            reason = getattr(batch_card, name)
            self.assertIn(reason, batch_card.REASONS)
            self.assertTrue(reason.endswith("\n"))
        self.assertIn("resolve --rows PATH --answer PATH [--prior-rows PATH]",
                      batch_card.USAGE)


# --------------------------------------------------------------------------- #
# Each resolve check is load-bearing: a mutant of it trips its lock.
# --------------------------------------------------------------------------- #
class TestResolveLockTrips(unittest.TestCase):
    """Each mutant first differs from the real output, then trips the lock
    check the real test uses. The parser is a second net for m5 only."""

    def test_m1_count_check_dropped(self):
        doc, refs = iplayarr_rows(), eight_row_refs(count=6)
        real = resolve(doc, refs)
        with self.subTest("real"):
            check_count_mismatch(self, real)
        with self.subTest("mutant: count check dropped"):
            with mock.patch.object(
                    batch_card, "_count_status",
                    lambda matched, count: "one" if matched else "none"):
                out = resolve(doc, refs)
            self.assertNotEqual(out, real)
            self.assertEqual(out["refs"][1]["status"], "one")
            with self.assertRaises(AssertionError):
                check_count_mismatch(self, out)

    def test_m2_many_treated_as_one(self):
        doc, refs = timeout_rows(), refs_doc([ref_title("fix", "timeout")])
        real = resolve(doc, refs)
        real_match = batch_card._match_title

        def first_only(rows, text):
            return real_match(rows, text)[:1]

        with self.subTest("real"):
            check_ambiguous_title(self, real)
        with self.subTest("mutant: many treated as one"):
            with mock.patch.object(batch_card, "_match_title", first_only):
                out = resolve(doc, refs)
            self.assertNotEqual(out, real)
            self.assertEqual(out["refs"][0]["status"], "one")
            with self.assertRaises(AssertionError):
                check_ambiguous_title(self, out)

    def test_m3_rest_for_counted_ref(self):
        doc, refs = iplayarr_rows(), eight_row_refs()
        real = resolve(doc, refs)
        real_grammar = batch_card._grammar_for

        def counted_as_rest(clauses, reason):
            return real_grammar([(v, "rest" if v == "dismiss" else spec)
                                 for v, spec in clauses], reason)

        with self.subTest("real"):
            check_no_broadening(self, doc, real)
        with self.subTest("mutant: rest emitted for a counted reference"):
            with mock.patch.object(batch_card, "_grammar_for",
                                   counted_as_rest):
                out = resolve(doc, refs)
            self.assertNotEqual(out["grammar"], real["grammar"])
            self.assertIn("dismiss rest", out["grammar"])
            with self.assertRaises(AssertionError):
                check_no_broadening(self, doc, out)

    def test_m4_hash_remap_skipped(self):
        prior, current = stale_pair()
        refs = refs_doc([ref_prior("fix", 7)])
        real = resolve(current, refs, prior)
        real_remap = batch_card._remap_prior

        def file_title_only(prior_row, rows):
            return real_remap(dict(prior_row, stable_hash="no such hash"),
                              rows)

        with self.subTest("real"):
            check_hash_remap(self, real, 5)
        with self.subTest("mutant: hash remap skipped"):
            with mock.patch.object(batch_card, "_remap_prior",
                                   file_title_only):
                out = resolve(current, refs, prior)
            self.assertNotEqual(out, real)
            self.assertEqual(out["refs"][0]["status"], "none")
            with self.assertRaises(AssertionError):
                check_hash_remap(self, out, 5)

    def test_m5_conflict_check_dropped(self):
        doc = iplayarr_rows()
        refs = refs_doc([ref_number("fix", 5), ref_number("dismiss", 5)],
                        reason="x")
        real = resolve(doc, refs)

        def reclaim(claimed, numbers):
            claimed.update(numbers)
            return True

        with self.subTest("real"):
            check_conflict(self, real)
        with self.subTest("mutant: conflict check dropped"):
            with mock.patch.object(batch_card, "_claim", reclaim):
                out = resolve(doc, refs)
            self.assertNotEqual(out, real)
            self.assertEqual(out["refs"][1]["status"], "one")
            # The parser still refuses the duplicate: a second net, not the
            # lock this test guards.
            self.assertEqual(out["parse_reason"],
                             batch_parse.REASON_DUPLICATE)
            with self.assertRaises(AssertionError):
                check_conflict(self, out)


class TestResolveCliContract(TempDirCase):
    """Refusals are fixed REASONS lines with no owner text; resolve reads no
    stdin."""

    def _run(self, refs, prior=None, stdin_bytes=b""):
        argv = ["resolve", "--rows", self.write("rows.json", iplayarr_rows()),
                "--answer", self.write("refs.json", refs)]
        if prior is not None:
            argv += ["--prior-rows", self.write("prior.json", prior)]
        return run_cli(argv, stdin_bytes=stdin_bytes)

    def test_refusals_are_reasons_without_owner_text(self):
        owner_words = ("Browse", "recovery", "zebra", "dismiss the 7")
        cases = {
            "bad verb": (refs_doc([dict(ref_title("fix", "Browse recovery"),
                                        verb="zebra")],
                                  reason=OWNER_REASON), None),
            "prior needed": (refs_doc([ref_prior("fix", 5)],
                                      reason=OWNER_REASON), None),
            "prior malformed": (refs_doc([ref_prior("fix", 5)],
                                         reason=OWNER_REASON),
                                {"title": "Browse zebra"}),
            "not json": ("Browse recovery zebra", None),
        }
        for name, (refs, prior) in cases.items():
            with self.subTest(name):
                proc = self._run(refs, prior)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                err = proc.stderr.decode()
                self.assertIn(err, RESOLVE_REASONS)
                for word in owner_words:
                    self.assertNotIn(word, err)

    def test_usage_refusals(self):
        rows = self.write("rows.json", iplayarr_rows())
        refs = self.write("refs.json", eight_row_refs())
        for argv in (["resolve", "--rows", rows],
                     ["resolve", "--answer", refs],
                     ["resolve", "--rows", rows, "--answer", refs, "--mode",
                      "fix-loop"],
                     ["resolve", "--rows", rows, "--answer", refs,
                      "--prior-rows"]):
            with self.subTest(argv=argv[1:]):
                proc = run_cli(argv)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stderr.decode(), batch_card.USAGE)

    def test_reads_no_stdin(self):
        proc = self._run(eight_row_refs(), stdin_bytes=b"garbage \xff")
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertTrue(json.loads(proc.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
