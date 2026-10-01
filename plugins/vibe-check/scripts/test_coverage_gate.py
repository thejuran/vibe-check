"""test_coverage_gate.py — the diff-mode test-sufficiency dispatch gate.

`coverage_gate.py` turns two path lists gathered in Phase 1d (`found`: every
coverage artifact the discovery globs matched; `injected`: the subset whose
content actually reached the `<coverage_data>` block) into a sealed
`{dispatch, case}` verdict.

Every golden here is a hand-computed literal, never produced by calling the
module. The malformed-input tests pin the fail-toward-dispatch contract: on any
malformed-but-parseable envelope the helper prints NOTHING on stdout and exits
2, so the orchestrator dispatches the lane exactly as it does today rather than
acting on a verdict that might be wrong. No test in this file writes a file.
"""

import ast
import json
import os
import subprocess
import sys
import unittest

# Make `import coverage_gate` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import coverage_gate  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
COVERAGE_GATE_PY = os.path.join(HERE, "coverage_gate.py")


# --------------------------------------------------------------------------- #
# GOLDEN — hand-computed literals, NOT produced by calling the module.
#
#   found=[]                              injected=[]   -> nothing discovered
#   found=[".coverage"]                   injected=[]   -> binary-only artifact,
#                                                          discovered but unusable
#   found=["coverage/lcov.info", ...]     injected=[]   -> discovered, none read
#   found=["coverage/lcov.info"]          injected=same -> block non-empty
#   found=["a.xml", "b.xml"]              injected=["b.xml"] -> partial, non-empty
# --------------------------------------------------------------------------- #
GOLDEN = [
    ({"found": [], "injected": []},
     {"dispatch": False, "case": "no-artifact"}),
    ({"found": [".coverage"], "injected": []},
     {"dispatch": False, "case": "none-usable"}),
    ({"found": ["coverage/lcov.info", "coverage.xml"], "injected": []},
     {"dispatch": False, "case": "none-usable"}),
    ({"found": ["coverage/lcov.info"], "injected": ["coverage/lcov.info"]},
     {"dispatch": True, "case": "present"}),
    ({"found": ["a.xml", "b.xml"], "injected": ["b.xml"]},
     {"dispatch": True, "case": "present"}),
]

# Each malformed envelope differs from a valid one by exactly one edit.
MALFORMED = [
    ("non-dict envelope", ["coverage.xml"]),
    ("missing injected", {"found": []}),
    ("missing found", {"injected": []}),
    ("extra key", {"found": [], "injected": [], "empty": True}),
    ("found is a str", {"found": "coverage.xml", "injected": []}),
    ("found is a dict", {"found": {}, "injected": []}),
    ("int element in found", {"found": [5], "injected": []}),
    ("empty-string element in injected",
     {"found": ["coverage.xml"], "injected": [""]}),
    ("bool element in found", {"found": [True], "injected": []}),
    ("injected with empty found", {"found": [], "injected": ["x"]}),
    ("injected not in found", {"found": ["y"], "injected": ["x"]}),
]


class TestGoldenDecisions(unittest.TestCase):
    def test_golden_rows_through_run(self):
        for envelope, expected in GOLDEN:
            with self.subTest(envelope=envelope):
                self.assertEqual(coverage_gate.run(envelope), expected)

    def test_golden_rows_through_decide(self):
        for envelope, expected in GOLDEN:
            with self.subTest(envelope=envelope):
                self.assertEqual(
                    coverage_gate.decide(envelope["found"],
                                         envelope["injected"]),
                    expected)

    def test_golden_table_is_what_we_think_it_is(self):
        """Fixture integrity: a table that read zero rows, or never hit one of
        the three cases, would pass vacuously."""
        self.assertEqual(len(GOLDEN), 5)
        seen = {expected["case"] for _, expected in GOLDEN}
        self.assertEqual(seen, {"present", "no-artifact", "none-usable"})

    def test_lone_dot_coverage_counts_as_found(self):
        """A binary `.coverage` is discovered but never readable, so the case
        is none-usable, not no-artifact."""
        self.assertEqual(
            coverage_gate.run({"found": [".coverage"], "injected": []}),
            {"dispatch": False, "case": "none-usable"})

    def test_decide_returns_a_fresh_dict(self):
        first = coverage_gate.decide([], [])
        first["case"] = "mutated"
        self.assertEqual(coverage_gate.decide([], []),
                         {"dispatch": False, "case": "no-artifact"})


class TestMalformedInput(unittest.TestCase):
    def test_every_malformed_envelope_returns_none(self):
        for label, bad in MALFORMED:
            with self.subTest(label=label):
                self.assertIsNone(coverage_gate.run(bad))

    def test_malformed_table_is_what_we_think_it_is(self):
        """Fixture integrity: the subset rule needs both a found=[] and a
        disjoint found=[...] row; the strict-type rule needs a bool row."""
        labels = {label for label, _ in MALFORMED}
        self.assertEqual(len(MALFORMED), 11)
        self.assertIn("injected with empty found", labels)
        self.assertIn("injected not in found", labels)
        self.assertIn("bool element in found", labels)


class TestSlugsLocked(unittest.TestCase):
    EXPECTED = ("present", "no-artifact", "none-usable")

    def test_cases_exact_tuple_in_order(self):
        self.assertEqual(coverage_gate.CASES, self.EXPECTED)

    def test_cases_is_an_immutable_tuple(self):
        self.assertIsInstance(coverage_gate.CASES, tuple)

    def test_every_golden_case_is_a_member(self):
        for envelope, _ in GOLDEN:
            with self.subTest(envelope=envelope):
                decision = coverage_gate.decide(envelope["found"],
                                                envelope["injected"])
                self.assertIn(decision["case"], coverage_gate.CASES)


class TestNoInventedSlugs(unittest.TestCase):
    """Every case slug in the module must come from CASES, never a bare literal.

    A hand-typed slug elsewhere in the file is how three cases drift into four.
    The tuple is the single site; every other reference is a name unpacked
    from it.
    """

    def _tree(self):
        with open(COVERAGE_GATE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def _exempt_ids(self, tree):
        exempt = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets
                           if isinstance(t, ast.Name)]
                if "CASES" in targets:
                    for sub in ast.walk(node.value):
                        if (isinstance(sub, ast.Constant)
                                and isinstance(sub.value, str)):
                            exempt.add(id(sub))
        return exempt

    def test_no_slug_string_literal_outside_the_tuple(self):
        tree = self._tree()
        exempt = self._exempt_ids(tree)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in exempt:
                    continue
                if node.value in coverage_gate.CASES:
                    offenders.append(node.value)
        self.assertEqual(
            offenders, [],
            "slug literals outside the CASES tuple: " + str(offenders))

    def test_the_exemption_actually_finds_the_tuple(self):
        """Fixture integrity: an exemption that matched nothing would make the
        walk above flag the tuple itself, and one that matched everything
        would make it vacuous. It must cover exactly the three slugs."""
        self.assertEqual(len(self._exempt_ids(self._tree())), 3)


class TestCLI(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, COVERAGE_GATE_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_golden_round_trips_through_the_shim(self):
        for envelope, expected in GOLDEN:
            with self.subTest(envelope=envelope):
                proc = self._run(json.dumps(envelope).encode())
                self.assertEqual(proc.returncode, 0, proc.stderr.decode())
                self.assertEqual(json.loads(proc.stdout.decode()), expected)

    def test_output_keys_are_exactly_dispatch_and_case(self):
        for envelope, _ in GOLDEN:
            with self.subTest(envelope=envelope):
                proc = self._run(json.dumps(envelope).encode())
                self.assertEqual(set(json.loads(proc.stdout.decode())),
                                 {"dispatch", "case"})

    def test_no_input_path_is_echoed(self):
        envelope = {"found": ["coverage/lcov.info"],
                    "injected": ["coverage/lcov.info"]}
        proc = self._run(json.dumps(envelope).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertNotIn(b"lcov.info", proc.stdout)
        self.assertNotIn(b"coverage/", proc.stdout)

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)

    def test_malformed_payload_exits_2_with_empty_stdout(self):
        for label, bad in MALFORMED:
            with self.subTest(label=label):
                proc = self._run(json.dumps(bad).encode())
                self.assertEqual(proc.returncode, 2, label)
                self.assertEqual(proc.stdout, b"", label)
                self.assertTrue(proc.stderr.startswith(b"refused:"),
                                proc.stderr)


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob", "re",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(COVERAGE_GATE_PY, "r", encoding="utf-8") as fh:
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
            "coverage_gate.py imports outside the allowed set: "
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
