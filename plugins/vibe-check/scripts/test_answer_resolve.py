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
        doc["rows"][0]["stale"] = {"decision": "dismiss"}
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
        self.assertEqual(batch_card.SUBCOMMANDS[-1], "resolve")
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
    def test_m1_count_check_dropped(self):
        self.skipTest("Task 3")

    def test_m2_many_treated_as_one(self):
        self.skipTest("Task 3")

    def test_m3_rest_for_counted_ref(self):
        self.skipTest("Task 3")

    def test_m4_hash_remap_skipped(self):
        self.skipTest("Task 3")

    def test_m5_conflict_check_dropped(self):
        self.skipTest("Task 3")


if __name__ == "__main__":
    unittest.main()
