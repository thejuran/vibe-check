"""test_coverage.py — the `--all` coverage note's R/T/S arithmetic.

The one rule this file exists to lock is the identity at `review.md:925`:

    {{S}} (SKIPPED) = {{T}} - {{R}} — EXACTLY, so R + S = T ALWAYS holds.

`S` is DERIVED, never counted. It is everything selected but not dispatched,
whether or not a skip reason was attributed to it. Fix-list FL-06 (finding R10)
caught a draft that redefined `S = sum(skip_reasons.values())`; the plan's own
worked example disproves that reading — `(T=10, R=7, {"skipped-binary": 1})`
yields S=1 under the counted definition and S=3 under the real one, and 3 is
correct because the other two files were skipped for reasons nobody attributed.

So attribution completeness is a SEPARATE diagnostic. `unattributed` carries it
as its own number, and the coverage note must never render buckets that do not
add up — that is the defect the extraction removes. Under-attribution shrinking
`S` would understate how much of the codebase went unreviewed, in a report whose
whole purpose is an honest audit denominator (`review.md:930`, the coverage
overstatement anti-pattern).

Symlinks are OUTSIDE the R/T/S arithmetic entirely (`review.md:926`, P10-C):
folding them into S would make R + S = T + symlinks > T. They ride alongside as
their own count and are asserted here to never move S.
"""

import ast
import json
import os
import subprocess
import sys
import unittest

# Make `import coverage` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import coverage  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
COVERAGE_PY = os.path.join(HERE, "coverage.py")


# --------------------------------------------------------------------------- #
# GOLDEN — one fixed input, one hand-computed literal.
#
# Computed independently, by hand, NOT by calling the module:
#   T = 12 (the $REVIEW_SET size)
#   R = 9  (the dispatched union)
#   S = 12 - 9 = 3
#   attributed = 2 + 1 = 3   -> unattributed = 3 - 3 = 0
#   identity_ok = True (S >= 0 and attribution does not exceed S)
# --------------------------------------------------------------------------- #
GOLDEN_INPUT = {
    "total": 12,
    "reviewed": 9,
    "skip_reasons": {"triage-skipped": 2, "capped": 1},
    "non_regular_skipped": 4,
}

GOLDEN_OUTPUT = {
    "T": 12,
    "R": 9,
    "S": 3,
    "skip_reasons": {"capped": 1, "triage-skipped": 2},
    "attributed": 3,
    "unattributed": 0,
    "unknown_reasons": [],
    "non_regular_skipped": 4,
    "identity_ok": True,
    "identity_error": None,
}


class TestGolden(unittest.TestCase):
    def test_golden_literal(self):
        self.assertEqual(coverage.compute(**GOLDEN_INPUT), GOLDEN_OUTPUT)

    def test_golden_input_is_what_we_think_it_is(self):
        """Fixture integrity: the golden must actually exercise attribution.

        A golden whose skip_reasons were empty would pass under both the real
        rule and FL-06's wrong one, proving nothing.
        """
        self.assertEqual(GOLDEN_INPUT["total"] - GOLDEN_INPUT["reviewed"], 3)
        self.assertEqual(sum(GOLDEN_INPUT["skip_reasons"].values()), 3)
        self.assertTrue(len(GOLDEN_INPUT["skip_reasons"]) >= 2)


class TestIdentityIsDerivedNotCounted(unittest.TestCase):
    """FL-06 / R10 — `S = T - R`, never `sum(skip_reasons)`.

    review.md:925 states the identity outright. These are the exact cases the
    fix-list names.
    """

    def test_fl06_worked_example_s_is_three_not_one(self):
        got = coverage.compute(10, 7, {"skipped-binary": 1})
        self.assertEqual(got["S"], 3, "S must be T-R (3), not the bucket sum (1)")
        self.assertEqual(got["unattributed"], 2)

    def test_unattributed_is_visible_not_silent(self):
        got = coverage.compute(10, 7, {"skipped-binary": 1})
        self.assertEqual(got["attributed"], 1)
        self.assertEqual(got["S"] - got["attributed"], got["unattributed"])

    def test_incomplete_attribution_is_not_an_identity_failure(self):
        """Under-attribution is a diagnostic, NOT a broken identity.

        The prose never requires the buckets to be complete — it requires
        R + S = T. Flagging incomplete attribution as identity_ok=False would
        make the healthy common case (some skips unattributed, `review.md:925`
        says "where the skip reasons are known") look like a bug.
        """
        got = coverage.compute(10, 7, {"skipped-binary": 1})
        self.assertTrue(got["identity_ok"])
        self.assertIsNone(got["identity_error"])

    def test_full_attribution_leaves_zero_unattributed(self):
        got = coverage.compute(10, 7, {"skipped-binary": 2, "skipped-vendored": 1})
        self.assertEqual(got["S"], 3)
        self.assertEqual(got["unattributed"], 0)
        self.assertTrue(got["identity_ok"])

    def test_over_attribution_breaks_the_identity(self):
        """More attributed skips than S means a bucket counts a file that was
        reviewed, or double-counts. Never render that."""
        got = coverage.compute(10, 7, {"skipped-binary": 5})
        self.assertFalse(got["identity_ok"])
        self.assertIsNotNone(got["identity_error"])
        self.assertIn("5", got["identity_error"])
        self.assertIn("3", got["identity_error"])

    def test_reviewed_exceeds_total_never_yields_negative_s(self):
        got = coverage.compute(7, 10, {})
        self.assertFalse(got["identity_ok"])
        self.assertIsNotNone(got["identity_error"])
        self.assertGreaterEqual(got["S"], 0, "never render a negative skipped count")

    def test_empty_run_is_all_zero_and_does_not_crash(self):
        got = coverage.compute(0, 0, {})
        self.assertEqual((got["T"], got["R"], got["S"]), (0, 0, 0))
        self.assertTrue(got["identity_ok"])
        self.assertEqual(got["unattributed"], 0)

    def test_identity_holds_across_many_shapes(self):
        for total, reviewed in ((0, 0), (1, 0), (1, 1), (50, 50), (200, 3)):
            with self.subTest(total=total, reviewed=reviewed):
                got = coverage.compute(total, reviewed, {})
                self.assertEqual(got["R"] + got["S"], got["T"])


class TestSymlinksOutsideArithmetic(unittest.TestCase):
    """review.md:926 (P10-C) — symlinks are OUTSIDE R/T/S."""

    def test_non_regular_never_moves_s(self):
        without = coverage.compute(10, 7, {}, non_regular_skipped=0)
        with_syms = coverage.compute(10, 7, {}, non_regular_skipped=5)
        self.assertEqual(without["S"], with_syms["S"])
        self.assertEqual(with_syms["non_regular_skipped"], 5)

    def test_non_regular_is_not_counted_as_attribution(self):
        got = coverage.compute(10, 7, {"capped": 3}, non_regular_skipped=5)
        self.assertEqual(got["attributed"], 3)
        self.assertEqual(got["unattributed"], 0)
        self.assertTrue(got["identity_ok"])


class TestBuckets(unittest.TestCase):
    def test_buckets_transcribed_from_prose(self):
        self.assertEqual(coverage.BUCKETS, ("capped", "triage-skipped"))

    def test_unknown_reason_is_flagged_never_dropped(self):
        """A silently dropped skip reason is invisible under-review."""
        got = coverage.compute(10, 7, {"capped": 1, "mystery-reason": 2})
        self.assertEqual(got["skip_reasons"]["mystery-reason"], 2)
        self.assertIn("mystery-reason", got["unknown_reasons"])
        self.assertNotIn("capped", got["unknown_reasons"])
        self.assertEqual(got["attributed"], 3)

    def test_unknown_reasons_are_sorted(self):
        got = coverage.compute(20, 10, {"zeta": 1, "alpha": 1})
        self.assertEqual(got["unknown_reasons"], ["alpha", "zeta"])


class TestFailClosed(unittest.TestCase):
    def test_non_int_total_refuses(self):
        for bad in ("10", None, 1.5, True, [10]):
            with self.subTest(bad=bad):
                got = coverage.compute(bad, 0, {})
                self.assertFalse(got["identity_ok"])
                self.assertIsNotNone(got["identity_error"])

    def test_negative_input_refuses(self):
        got = coverage.compute(-1, 0, {})
        self.assertFalse(got["identity_ok"])

    def test_non_dict_reasons_refuses(self):
        got = coverage.compute(10, 7, ["capped"])
        self.assertFalse(got["identity_ok"])

    def test_non_int_reason_count_refuses(self):
        got = coverage.compute(10, 7, {"capped": "3"})
        self.assertFalse(got["identity_ok"])

    def test_run_rejects_non_dict_envelope(self):
        self.assertFalse(coverage.run(["not", "a", "dict"])["identity_ok"])


class TestNoRendering(unittest.TestCase):
    """D-08 boundary, made executable.

    The prose renders the coverage note (`review.md:922`); this module only
    computes the numbers. If a rendered fragment ever appears in the output,
    the keep-list has been crossed.
    """

    FORBIDDEN_CHARS = ("|", "%", "{{", "⚠", "\n")

    def _all_strings(self, obj):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from self._all_strings(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                yield from self._all_strings(v)

    def test_no_rendered_fragment_in_output(self):
        cases = (
            coverage.compute(**GOLDEN_INPUT),
            coverage.compute(10, 7, {"skipped-binary": 5}),
            coverage.compute(7, 10, {}),
            coverage.compute("bad", 0, {}),
        )
        for i, out in enumerate(cases):
            for s in self._all_strings(out):
                with self.subTest(case=i, s=s):
                    for ch in self.FORBIDDEN_CHARS:
                        self.assertNotIn(ch, s)

    def test_the_forbidden_char_guard_is_not_vacuous(self):
        """Prove the guard trips on the defect it targets.

        A rendered coverage note is exactly the kind of string this must
        reject; if the checker passed it, the whole class would be decorative.
        """
        rendered = {"note": "Reviewed 9 of 12 files (75%)"}
        tripped = False
        for s in self._all_strings(rendered):
            for ch in self.FORBIDDEN_CHARS:
                if ch in s:
                    tripped = True
        self.assertTrue(tripped, "guard failed to reject a rendered note")


class TestCLI(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, COVERAGE_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_golden_round_trips_through_the_shim(self):
        proc = self._run(json.dumps(GOLDEN_INPUT).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode()), GOLDEN_OUTPUT)

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)


class TestCitations(unittest.TestCase):
    def _source(self):
        with open(COVERAGE_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_module_cites_review_md_lines(self):
        self.assertIn("review.md:925", self._source())

    def test_module_states_the_d08_boundary(self):
        src = self._source().lower()
        self.assertIn("prose renders", src)


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob", "re",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(COVERAGE_PY, "r", encoding="utf-8") as fh:
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
            "coverage.py imports outside the allowed set: "
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
        """Fixture integrity: an AST walk that found nothing would pass
        vacuously."""
        self.assertEqual(self._imported(), self.ALLOWED)


if __name__ == "__main__":
    unittest.main()
