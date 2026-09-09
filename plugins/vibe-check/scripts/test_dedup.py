"""test_dedup.py — the `--all` cross-file dedup GROUPING rule.

Transcribed from `review.md:948` (the grouping key) and `:949` (the 2+-distinct-
files collapse condition). This module groups; the prose renders. The grouping
is RENDER-ONLY in the orchestrator's sense — `review.md:947` is emphatic that no
canonical finding object is altered, merged, removed or re-scored — so `group()`
returns references (finding ids) into the caller's unchanged finding list and
never the findings themselves.

Two properties are load-bearing:

* CONSERVATISM. `review.md:948` says the ≥0.7 Jaccard bar is "deliberately
  conservative so two genuinely DISTINCT bugs that merely share a `category` are
  NEVER merged into one displayed row." A test asserts a same-category pair with
  disjoint titles stays in two groups.
* DETERMINISM. A grouping whose output order depended on input order would make
  the rendered report unstable run-to-run, which is exactly what DIET-04's
  envelope leg measures. The shuffle test locks a total order over 24
  permutations. Note the tie-break within a group — `(file, line, id)` — is NEW:
  the prose left member order unspecified. It is documented as new in dedup.py's
  docstring rather than presented as transcribed.
"""

import ast
import copy
import json
import os
import random
import subprocess
import sys
import unittest

# Make `import dedup` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dedup  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
DEDUP_PY = os.path.join(HERE, "dedup.py")


def f(fid, category, title, path, line, score=50):
    return {"id": fid, "category": category, "title": title,
            "file": path, "line": line, "orchestrator_score": score}


# --------------------------------------------------------------------------- #
# GOLDEN — one fixed finding set, one hand-computed literal.
#
# Worked by hand, NOT by calling the module:
#   a1 normalizes to {sql, injection, in}: `build_query` is a stripped quoted
#   identifier, so `query` is NOT in a1's set.
#   a2 normalizes to {sql, injection, in, at, query}: the path and the line
#   number are stripped, `at` and `query` are ordinary words that survive.
#   Jaccard(a1,a2) = 3/5 = 0.6, BELOW the 0.7 bar — so this pair groups ONLY
#   via :948's SECOND arm, set-containment after the strip (a1 subset of a2).
#   That makes the golden a load-bearing test of the substring arm; see
#   test_golden_groups_via_the_containment_arm_not_jaccard below.
#   Same category, 2 distinct files -> ONE collapsed group, primary = the
#   higher score (a2, 90) -> members ordered by (file, line, id):
#     ("api/orders.py", 12, "a2") < ("api/users.py", 4, "a1")
#   b1 shares no normalized token with them -> its own group of one, and with
#   only 1 distinct file it does not collapse.
#   Group order: collapsed groups first (by descending primary score), then the
#   rest — see dedup.py's ORDER note.
# --------------------------------------------------------------------------- #
GOLDEN_INPUT = [
    f("a1", "security", "SQL injection in `build_query`", "api/users.py", 4, 70),
    f("b1", "bugs", "Unhandled None from cache lookup", "core/cache.py", 88, 60),
    f("a2", "security", "SQL injection in query at api/orders.py:12",
      "api/orders.py", 12, 90),
]

GOLDEN_OUTPUT = [
    {
        # The key is built from the group's SEED — a2, visited first under the
        # (file, line, id) order because "api/orders.py" < "api/users.py".
        "key": "security::at|in|injection|query|sql",
        "members": ["a2", "a1"],
        "files": ["api/orders.py", "api/users.py"],
        "primary": "a2",
        "occurrence_count": 2,
        "collapsed": True,
    },
    {
        "key": "bugs::cache|from|lookup|none|unhandled",
        "members": ["b1"],
        "files": ["core/cache.py"],
        "primary": "b1",
        "occurrence_count": 1,
        "collapsed": False,
    },
]


class TestGolden(unittest.TestCase):
    def test_golden_literal(self):
        self.assertEqual(dedup.group(GOLDEN_INPUT), GOLDEN_OUTPUT)

    def test_golden_fixture_is_what_we_think_it_is(self):
        """Fixture integrity.

        The golden is only meaningful if it actually contains a cross-file pair
        AND a loner. A fixture that collapsed to one group, or to three, would
        silently stop exercising the collapse condition.
        """
        self.assertEqual(len(GOLDEN_INPUT), 3)
        self.assertEqual(len({x["id"] for x in GOLDEN_INPUT}), 3)
        self.assertEqual(len({x["file"] for x in GOLDEN_INPUT}), 3)
        # a1/a2 share a category; b1 does not.
        self.assertEqual(GOLDEN_INPUT[0]["category"], GOLDEN_INPUT[2]["category"])
        self.assertNotEqual(GOLDEN_INPUT[1]["category"],
                            GOLDEN_INPUT[0]["category"])
        # And the expectation itself: exactly one group collapses.
        self.assertEqual(sum(1 for g in GOLDEN_OUTPUT if g["collapsed"]), 1)

    def test_golden_groups_via_the_containment_arm_not_jaccard(self):
        """Fixture integrity, and a load-bearing check of :948's second arm.

        The hand-computed expectation for this golden was initially wrong: it
        assumed `build_query` contributed a `query` token to a1. It does not —
        it is a quoted identifier and is stripped. The real Jaccard is 3/5 =
        0.6, BELOW the 0.7 bar, so this pair groups only because a1's token set
        is contained in a2's. Asserting that here means a regression that
        deleted the containment arm would fail loudly instead of quietly
        splitting the golden into two groups.
        """
        a1 = dedup._normalize(GOLDEN_INPUT[0]["title"])
        a2 = dedup._normalize(GOLDEN_INPUT[2]["title"])
        self.assertEqual(a1, {"sql", "injection", "in"})
        self.assertEqual(a2, {"sql", "injection", "in", "at", "query"})
        jaccard = len(a1 & a2) / len(a1 | a2)
        self.assertAlmostEqual(jaccard, 0.6)
        self.assertLess(jaccard, dedup.JACCARD_THRESHOLD,
                        "golden must NOT be groupable by Jaccard alone")
        self.assertTrue(a1 <= a2, "containment is the arm under test")
        self.assertTrue(dedup._similar(a2, a1))

    def test_group_does_not_mutate_the_input(self):
        """review.md:947 — the grouping alters no canonical finding object."""
        before = copy.deepcopy(GOLDEN_INPUT)
        dedup.group(GOLDEN_INPUT)
        self.assertEqual(GOLDEN_INPUT, before)


class TestGroupingKey(unittest.TestCase):
    """review.md:948 — IDENTICAL category AND substantially-similar title."""

    def test_same_key_across_files_makes_one_group(self):
        got = dedup.group([
            f("x", "security", "Missing auth check on handler", "a.py", 1),
            f("y", "security", "Missing auth check on handler", "b.py", 2),
        ])
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["members"], ["x", "y"])
        self.assertEqual(got[0]["files"], ["a.py", "b.py"])

    def test_identical_title_but_different_category_never_groups(self):
        """`category` must be IDENTICAL — similarity does not span categories."""
        got = dedup.group([
            f("x", "security", "Missing auth check", "a.py", 1),
            f("y", "bugs", "Missing auth check", "b.py", 2),
        ])
        self.assertEqual(len(got), 2)

    def test_distinct_bugs_sharing_a_category_are_never_merged(self):
        """The conservatism clause at :948, stated as a test."""
        got = dedup.group([
            f("x", "bugs", "Race condition in scheduler", "a.py", 1),
            f("y", "bugs", "Leaked file descriptor", "b.py", 2),
        ])
        self.assertEqual(len(got), 2)

    def test_substring_after_strip_groups(self):
        """:948 — "OR one normalized title is a substring of the other"."""
        got = dedup.group([
            f("x", "security", "Hardcoded secret", "a.py", 1),
            f("y", "security", "Hardcoded secret in the deploy script",
              "b.py", 2),
        ])
        self.assertEqual(len(got), 1, got)

    def test_jaccard_bar_is_seven_tenths(self):
        """Below the bar stays split; at-or-above the bar groups.

        Titles are built so the overlap is computable by hand:
          x tokens {alpha, beta, gamma, delta}, y adds {epsilon}
          -> intersection 4, union 5, Jaccard 0.8 >= 0.7  -> grouped
          x vs z tokens {alpha, beta, gamma, delta} vs {alpha, beta, one, two}
          -> intersection 2, union 6, Jaccard 0.333 < 0.7 -> split
        """
        grouped = dedup.group([
            f("x", "bugs", "alpha beta gamma delta", "a.py", 1),
            f("y", "bugs", "alpha beta gamma delta epsilon", "b.py", 2),
        ])
        self.assertEqual(len(grouped), 1)
        split = dedup.group([
            f("x", "bugs", "alpha beta gamma delta", "a.py", 1),
            f("z", "bugs", "alpha beta one two", "b.py", 2),
        ])
        self.assertEqual(len(split), 2)

    def test_normalization_strips_paths_symbols_and_line_numbers(self):
        """:948 — "strip file-specific tokens (paths, identifiers, quoted
        symbols, and line numbers)"."""
        got = dedup.group([
            f("x", "bugs", "Null deref in `parse_row` at src/a/b.py:41",
              "src/a/b.py", 41),
            f("y", "bugs", "Null deref in `parse_row` at lib/z.py:9",
              "lib/z.py", 9),
        ])
        self.assertEqual(len(got), 1, got)

    def test_case_is_folded(self):
        got = dedup.group([
            f("x", "bugs", "MISSING TIMEOUT", "a.py", 1),
            f("y", "bugs", "missing timeout", "b.py", 2),
        ])
        self.assertEqual(len(got), 1)


class TestCollapseCondition(unittest.TestCase):
    """review.md:949 — collapse applies to groups spanning 2+ DISTINCT files."""

    def test_same_file_twice_does_not_collapse(self):
        got = dedup.group([
            f("x", "bugs", "Missing timeout", "a.py", 1),
            f("y", "bugs", "Missing timeout", "a.py", 9),
        ])
        self.assertEqual(len(got), 1)
        self.assertFalse(got[0]["collapsed"])
        self.assertEqual(got[0]["files"], ["a.py"])
        self.assertEqual(got[0]["occurrence_count"], 2)

    def test_lone_finding_is_a_group_of_one_uncollapsed(self):
        """:951 — "Ungrouped findings render normally", one row each."""
        got = dedup.group([f("x", "bugs", "Solo problem", "a.py", 1)])
        self.assertEqual(len(got), 1)
        self.assertFalse(got[0]["collapsed"])
        self.assertEqual(got[0]["members"], ["x"])

    def test_primary_is_the_highest_scored_occurrence(self):
        got = dedup.group([
            f("lo", "bugs", "Missing timeout", "a.py", 1, score=55),
            f("hi", "bugs", "Missing timeout", "b.py", 2, score=95),
        ])
        self.assertEqual(got[0]["primary"], "hi")

    def test_empty_input_is_empty_output(self):
        self.assertEqual(dedup.group([]), [])


class TestDeterministicUnderShuffle(unittest.TestCase):
    """The report's byte-stability depends on a total order."""

    FIXTURE = [
        f("m1", "security", "SQL injection in query", "z/last.py", 5, 80),
        f("m2", "security", "SQL injection in query", "a/first.py", 5, 80),
        f("m3", "security", "SQL injection in query", "a/first.py", 2, 80),
        f("n1", "bugs", "Unhandled timeout on fetch", "b/mid.py", 7, 60),
        f("n2", "bugs", "Unhandled timeout on fetch", "c/other.py", 7, 60),
        f("p1", "idiom", "Prefer pathlib over string joins", "d/one.py", 1, 30),
    ]

    def test_fixture_is_what_we_think_it_is(self):
        """Fixture integrity — the shuffle test is only meaningful if the
        fixture has ties that a naive order would resolve differently.

        m2/m3 share a file (line tie-break must decide), m1/m2/m3 share a score
        (so the primary pick must tie-break too), and n1/n2 form a second
        collapsed group with an identical score.
        """
        self.assertEqual(len(self.FIXTURE), 6)
        self.assertEqual(len({x["id"] for x in self.FIXTURE}), 6)
        scores = [x["orchestrator_score"] for x in self.FIXTURE]
        self.assertEqual(scores.count(80), 3, "need a 3-way score tie")
        files = [x["file"] for x in self.FIXTURE]
        self.assertEqual(files.count("a/first.py"), 2, "need a same-file pair")
        baseline = dedup.group(self.FIXTURE)
        self.assertEqual(len(baseline), 3, "expected 3 groups")
        self.assertEqual(sum(1 for g in baseline if g["collapsed"]), 2)

    def test_byte_identical_across_24_permutations(self):
        baseline = json.dumps(dedup.group(self.FIXTURE), sort_keys=False)
        rng = random.Random(20260908)
        for i in range(24):
            shuffled = list(self.FIXTURE)
            rng.shuffle(shuffled)
            with self.subTest(permutation=i):
                self.assertEqual(
                    json.dumps(dedup.group(shuffled), sort_keys=False),
                    baseline)

    def test_the_shuffle_actually_shuffles(self):
        """Fixture integrity: a seeded shuffle that returned the input
        unchanged would make the determinism test vacuous."""
        rng = random.Random(20260908)
        seen_reordered = False
        for _ in range(24):
            shuffled = list(self.FIXTURE)
            rng.shuffle(shuffled)
            if [x["id"] for x in shuffled] != [x["id"] for x in self.FIXTURE]:
                seen_reordered = True
        self.assertTrue(seen_reordered, "the shuffle never reordered anything")

    def test_members_sorted_by_file_line_id(self):
        got = dedup.group(self.FIXTURE)
        collapsed = [g for g in got if g["collapsed"] and len(g["members"]) == 3]
        self.assertEqual(len(collapsed), 1)
        # a/first.py:2 < a/first.py:5 < z/last.py:5
        self.assertEqual(collapsed[0]["members"], ["m3", "m2", "m1"])


class TestFailClosed(unittest.TestCase):
    def test_non_list_input_returns_empty(self):
        for bad in (None, "findings", {"a": 1}, 7):
            with self.subTest(bad=bad):
                self.assertEqual(dedup.group(bad), [])

    def test_malformed_member_is_skipped_not_crashed(self):
        got = dedup.group([
            f("ok", "bugs", "Missing timeout", "a.py", 1),
            {"id": "bad"},          # no category/title
            "not even a dict",
        ])
        self.assertEqual([g["members"] for g in got], [["ok"]])

    def test_run_rejects_non_dict_envelope(self):
        self.assertEqual(dedup.run("nope"), [])

    def test_run_reads_the_findings_key(self):
        self.assertEqual(dedup.run({"findings": GOLDEN_INPUT}), GOLDEN_OUTPUT)


class TestNoRendering(unittest.TestCase):
    """D-08 — grouping is executable, the grouped DISPLAY stays prose."""

    FORBIDDEN_CHARS = ("|", "%", "{{", "\n")

    def _all_values(self, obj):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, dict):
            for v in obj.values():
                yield from self._all_values(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                yield from self._all_values(v)

    def test_no_rendered_row_in_output(self):
        for g in dedup.group(GOLDEN_INPUT):
            for s in self._all_values(g):
                if s == g.get("key"):
                    continue  # the key is a join, not a rendered row
                with self.subTest(s=s):
                    for ch in self.FORBIDDEN_CHARS:
                        self.assertNotIn(ch, s)

    def test_no_occurrence_phrase_is_emitted(self):
        """:949 renders `(+ N more occurrences)`; this module emits the NUMBER
        and lets the prose write the phrase."""
        blob = json.dumps(dedup.group(GOLDEN_INPUT))
        self.assertNotIn("more occurrences", blob)

    def test_the_rendering_guard_is_not_vacuous(self):
        rendered = {"row": "api/users.py:4 | (+ 1 more occurrences)"}
        tripped = any(ch in s
                      for s in self._all_values(rendered)
                      for ch in self.FORBIDDEN_CHARS)
        self.assertTrue(tripped, "guard failed to reject a rendered row")


class TestCLI(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, DEDUP_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_golden_round_trips_through_the_shim(self):
        proc = self._run(json.dumps({"findings": GOLDEN_INPUT}).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode()), GOLDEN_OUTPUT)

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)


class TestCitations(unittest.TestCase):
    def _source(self):
        with open(DEDUP_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_module_cites_the_grouping_key_line(self):
        self.assertIn("review.md:948", self._source())

    def test_module_declares_the_tie_break_as_new(self):
        self.assertIn("NEW", self._source())

    def test_module_states_the_d08_boundary(self):
        """Whitespace-collapsed: the sentence wraps in the docstring."""
        src = " ".join(self._source().lower().split())
        self.assertIn("it groups; the prose renders", src)


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(DEDUP_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def _imported(self):
        imported = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        return imported

    def test_import_set_subset_of_allowed(self):
        imported = self._imported()
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "dedup.py imports outside the allowed set: "
            + str(imported - self.ALLOWED))

    def test_no_forbidden_module_imported(self):
        for name in self._imported():
            self.assertNotIn(name, self.FORBIDDEN_NAMES)

    def test_no_forbidden_calls(self):
        banned = {"eval", "exec", "compile", "__import__", "open"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned)

    def test_the_import_checker_actually_sees_imports(self):
        self.assertEqual(self._imported(), self.ALLOWED)


if __name__ == "__main__":
    unittest.main()
