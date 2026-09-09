"""test_codex_gate.py — the Codex diff-representability predicate.

The gate decides whether Codex runs at all. Its safety property is one
direction only: a wrong SKIP costs a second opinion, a wrong RUN means Codex
reviews a range that is not the range the orchestrator resolved — and
deep-review.md:222 spells out why that is the dangerous direction, since the
later `in_diff` clip can drop EXTRA findings but cannot recover defects Codex
never reviewed. So every ambiguity resolves to skip.

Two properties are load-bearing:

* The nine reason slugs are SEALED. Each names a distinct outcome that the
  Phase-3 status line renders verbatim (deep-review.md:355), and inventing a
  tenth would render an unrecognized line. TestSlugsLocked pins the tuple and
  TestNoInventedSlugs asserts no other slug-shaped literal exists in the module.
* Fail-closed is the DEFAULT, not an exception path. An unknown mode, a missing
  fact, or a non-bool fact must skip — never fall through to a run.

Ordering is transcribed from deep-review.md Phase 2c steps 1-5, not from the
plan's summary of them: step 1 not-installed, step 2 the probe
(unauthenticated / unavailable), step 4 diff-targeting (`--all` evaluated first
within it), step 5 no-timeout-binary. See the module docstring of codex_gate.py
for the citation of each.
"""

import ast
import json
import os
import re
import subprocess
import sys
import unittest

# Make `import codex_gate` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import codex_gate  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
CODEX_GATE_PY = os.path.join(HERE, "codex_gate.py")

ALL_TRUE = {
    "installed": True,
    "authenticated": True,
    "available": True,
    "timeout_binary": True,
    "dirty": False,
    "phase_start_is_ancestor": True,
    "head_is_upper": True,
    "a_is_ancestor_of_b": True,
    "head_is_pr_head": True,
    "merge_base_matches_pr_base": True,
}

WORKING_TREE_ARGS = ["--scope", "working-tree"]
BRANCH_ARGS = ["--base", "<base-ref>", "--scope", "branch"]


def facts(**overrides):
    f = dict(ALL_TRUE)
    f.update(overrides)
    return f


class TestSlugsLocked(unittest.TestCase):
    """The nine slugs are sealed — deep-review.md:355."""

    EXPECTED = (
        "not-installed",
        "unauthenticated",
        "unavailable",
        "whole-repo-non-representable",
        "phase-diff-has-uncommitted-tail",
        "range-not-identical",
        "head-not-at-target",
        "no-timeout-binary",
        "timeout",
    )

    def test_slugs_exact_tuple_in_order(self):
        self.assertEqual(codex_gate.SLUGS, self.EXPECTED)

    def test_slugs_is_an_immutable_tuple(self):
        self.assertIsInstance(codex_gate.SLUGS, tuple)

    def test_every_emitted_slug_is_a_member(self):
        """No decision may emit a slug outside the sealed set."""
        modes = ["all", "default", "gsd-empty-range", "gsd-range", "pr",
                 "range", "bogus"]
        variants = [
            {}, {"installed": False}, {"authenticated": False},
            {"available": False}, {"timeout_binary": False}, {"dirty": True},
            {"phase_start_is_ancestor": False}, {"head_is_upper": False},
            {"a_is_ancestor_of_b": False}, {"head_is_pr_head": False},
            {"merge_base_matches_pr_base": False},
        ]
        for mode in modes:
            for override in variants:
                decision = codex_gate.decide(mode, facts(**override))
                if decision["slug"] is not None:
                    self.assertIn(decision["slug"], codex_gate.SLUGS,
                                  "%s / %s emitted an unsealed slug"
                                  % (mode, override))


class TestAllFirst(unittest.TestCase):
    def test_all_mode_is_never_representable(self):
        decision = codex_gate.decide("all", facts())
        self.assertEqual(decision["action"], "skip")
        self.assertEqual(decision["slug"], "whole-repo-non-representable")
        self.assertIsNone(decision["codex_args"])

    def test_install_check_precedes_the_all_arm(self):
        """deep-review.md:215 step 1 runs before step 4's diff-targeting."""
        decision = codex_gate.decide("all", facts(installed=False))
        self.assertEqual(decision["slug"], "not-installed")

    def test_probe_precedes_the_all_arm(self):
        """Step 2 (probe) also precedes step 4 — the prose order, not the
        plan's summary, which put `all` before the probe."""
        self.assertEqual(
            codex_gate.decide("all", facts(authenticated=False))["slug"],
            "unauthenticated")
        self.assertEqual(
            codex_gate.decide("all", facts(available=False))["slug"],
            "unavailable")

    def test_all_mode_skips_before_the_timeout_binary_check(self):
        """Step 4 (diff-targeting) precedes step 5 (the launch guard), so the
        representability slug is the one reported."""
        decision = codex_gate.decide("all", facts(timeout_binary=False))
        self.assertEqual(decision["action"], "skip")
        self.assertEqual(decision["slug"], "whole-repo-non-representable")


class TestProbeOrder(unittest.TestCase):
    def test_not_installed_wins_over_unauthenticated(self):
        decision = codex_gate.decide(
            "default", facts(installed=False, authenticated=False))
        self.assertEqual(decision["slug"], "not-installed")

    def test_unauthenticated_wins_over_unavailable(self):
        decision = codex_gate.decide(
            "default", facts(authenticated=False, available=False))
        self.assertEqual(decision["slug"], "unauthenticated")

    def test_unavailable(self):
        self.assertEqual(
            codex_gate.decide("default", facts(available=False))["slug"],
            "unavailable")


class TestDefaultRuns(unittest.TestCase):
    def test_default_mode_runs_working_tree(self):
        decision = codex_gate.decide("default", facts())
        self.assertEqual(decision["action"], "run")
        self.assertIsNone(decision["slug"])
        self.assertEqual(decision["codex_args"], WORKING_TREE_ARGS)

    def test_default_mode_ignores_dirty(self):
        """The working tree IS the Phase-0 diff — no mismatch is possible."""
        decision = codex_gate.decide("default", facts(dirty=True))
        self.assertEqual(decision["action"], "run")
        self.assertEqual(decision["codex_args"], WORKING_TREE_ARGS)

    def test_gsd_empty_range_runs_working_tree(self):
        decision = codex_gate.decide("gsd-empty-range", facts())
        self.assertEqual(decision["action"], "run")
        self.assertEqual(decision["codex_args"], WORKING_TREE_ARGS)

    def test_working_tree_args_never_carry_a_base(self):
        """deep-review.md:266 — `--base ""` would force branch mode and review
        the WRONG range."""
        for mode in ("default", "gsd-empty-range"):
            self.assertNotIn(
                "--base", codex_gate.decide(mode, facts())["codex_args"])


class TestGsdRange(unittest.TestCase):
    def test_dirty_tail_skips(self):
        decision = codex_gate.decide("gsd-range", facts(dirty=True))
        self.assertEqual(decision["action"], "skip")
        self.assertEqual(decision["slug"], "phase-diff-has-uncommitted-tail")

    def test_non_ancestor_skips(self):
        decision = codex_gate.decide(
            "gsd-range", facts(phase_start_is_ancestor=False))
        self.assertEqual(decision["slug"], "range-not-identical")

    def test_dirty_wins_over_non_ancestor(self):
        decision = codex_gate.decide(
            "gsd-range", facts(dirty=True, phase_start_is_ancestor=False))
        self.assertEqual(decision["slug"], "phase-diff-has-uncommitted-tail")

    def test_clean_ancestor_runs_branch_mode(self):
        decision = codex_gate.decide("gsd-range", facts())
        self.assertEqual(decision["action"], "run")
        self.assertEqual(decision["codex_args"], BRANCH_ARGS)

    def test_base_ref_is_a_placeholder_not_a_resolved_ref(self):
        """The ref is substituted by bash — deep-review.md:251, `--base` is
        always the orchestrator's OWN resolved ref, never derived here."""
        self.assertEqual(codex_gate.BASE_REF_PLACEHOLDER, "<base-ref>")
        args = codex_gate.decide("gsd-range", facts())["codex_args"]
        self.assertEqual(args[args.index("--base") + 1], "<base-ref>")


class TestRange(unittest.TestCase):
    def test_head_not_at_upper_ref(self):
        decision = codex_gate.decide("range", facts(head_is_upper=False))
        self.assertEqual(decision["slug"], "head-not-at-target")

    def test_a_not_ancestor_of_b(self):
        decision = codex_gate.decide("range", facts(a_is_ancestor_of_b=False))
        self.assertEqual(decision["slug"], "range-not-identical")

    def test_head_check_precedes_the_ancestor_check(self):
        decision = codex_gate.decide(
            "range", facts(head_is_upper=False, a_is_ancestor_of_b=False))
        self.assertEqual(decision["slug"], "head-not-at-target")

    def test_both_identical_runs_branch_mode(self):
        decision = codex_gate.decide("range", facts())
        self.assertEqual(decision["action"], "run")
        self.assertEqual(decision["codex_args"], BRANCH_ARGS)


class TestPr(unittest.TestCase):
    def test_head_not_pr_head(self):
        decision = codex_gate.decide("pr", facts(head_is_pr_head=False))
        self.assertEqual(decision["slug"], "head-not-at-target")

    def test_merge_base_mismatch(self):
        decision = codex_gate.decide(
            "pr", facts(merge_base_matches_pr_base=False))
        self.assertEqual(decision["slug"], "range-not-identical")

    def test_both_identical_runs_branch_mode(self):
        decision = codex_gate.decide("pr", facts())
        self.assertEqual(decision["action"], "run")
        self.assertEqual(decision["codex_args"], BRANCH_ARGS)


class TestNoTimeoutBinary(unittest.TestCase):
    """deep-review.md:266 — the watchdog is inexpressible, so do NOT launch."""

    def test_run_mode_without_timeout_binary_skips(self):
        for mode in ("default", "gsd-empty-range", "gsd-range", "range", "pr"):
            decision = codex_gate.decide(mode, facts(timeout_binary=False))
            self.assertEqual(decision["action"], "skip", mode)
            self.assertEqual(decision["slug"], "no-timeout-binary", mode)
            self.assertIsNone(decision["codex_args"], mode)

    def test_representability_skip_is_reported_over_the_timeout_binary(self):
        """A range that is not representable stays labeled as such — the two
        slugs mean different things and must not be conflated."""
        decision = codex_gate.decide(
            "gsd-range", facts(dirty=True, timeout_binary=False))
        self.assertEqual(decision["slug"], "phase-diff-has-uncommitted-tail")


class TestFailClosed(unittest.TestCase):
    def test_unknown_mode(self):
        decision = codex_gate.decide("bogus", facts())
        self.assertEqual(decision["action"], "skip")
        self.assertEqual(decision["slug"], "range-not-identical")
        self.assertIsNone(decision["codex_args"])

    def test_non_string_mode(self):
        self.assertEqual(codex_gate.decide(None, facts())["action"], "skip")
        self.assertEqual(codex_gate.decide(7, facts())["action"], "skip")

    def test_missing_fact(self):
        for key in ALL_TRUE:
            partial = facts()
            del partial[key]
            decision = codex_gate.decide("default", partial)
            self.assertEqual(decision["action"], "skip", key)
            self.assertEqual(decision["slug"], "range-not-identical", key)

    def test_non_bool_fact(self):
        for value in ("true", 1, 0, None, [], {}):
            decision = codex_gate.decide("default", facts(installed=value))
            self.assertEqual(decision["action"], "skip", repr(value))
            self.assertEqual(decision["slug"], "range-not-identical",
                             repr(value))

    def test_int_one_is_not_accepted_as_true(self):
        """`1` is truthy but not a bool — bash emitting `1` instead of `true`
        must fail closed rather than be silently coerced."""
        self.assertEqual(
            codex_gate.decide("default", facts(installed=1))["action"], "skip")

    def test_facts_not_a_dict(self):
        for bad in (None, [], "facts", 3):
            self.assertEqual(codex_gate.decide("default", bad)["action"], "skip")

    def test_extra_facts_are_tolerated(self):
        """An unknown extra key is not a reason to refuse a valid decision."""
        decision = codex_gate.decide("default", facts(unexpected=True))
        self.assertEqual(decision["action"], "run")

    def test_decide_never_mutates_the_caller_facts(self):
        given = facts()
        snapshot = dict(given)
        codex_gate.decide("default", given)
        self.assertEqual(given, snapshot)


class TestRunEnvelope(unittest.TestCase):
    def test_run_threads_the_envelope(self):
        out = codex_gate.run({"mode": "default", "facts": facts()})
        self.assertEqual(out["action"], "run")

    def test_run_with_missing_keys_fails_closed(self):
        self.assertEqual(codex_gate.run({})["action"], "skip")
        self.assertEqual(codex_gate.run({})["slug"], "range-not-identical")

    def test_decision_key_set_is_stable(self):
        self.assertEqual(
            set(codex_gate.run({"mode": "all", "facts": facts()})),
            {"action", "slug", "codex_args"},
        )


class TestCLI(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, CODEX_GATE_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_default_all_true_prints_run(self):
        payload = json.dumps({"mode": "default", "facts": ALL_TRUE}).encode()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode())["action"], "run")

    def test_bogus_mode_prints_the_fail_closed_slug(self):
        payload = json.dumps({"mode": "bogus", "facts": {}}).encode()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode())["slug"],
                         "range-not-identical")

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)


class TestNoInventedSlugs(unittest.TestCase):
    """Every slug in the module must come from SLUGS, never a bare literal.

    A hand-typed slug elsewhere in the file is exactly how the nine drift into
    ten. The tuple is the single site; every other reference is an index into
    it.
    """

    SLUG_SHAPE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$")

    def test_no_slug_string_literal_outside_the_tuple(self):
        with open(CODEX_GATE_PY, "r", encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source)
        # Locate the SLUGS assignment so its own literals are exempt.
        exempt = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if "SLUGS" in targets:
                    for sub in ast.walk(node.value):
                        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                            exempt.add(id(sub))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in exempt:
                    continue
                if node.value in codex_gate.SLUGS:
                    offenders.append(node.value)
        self.assertEqual(
            offenders, [],
            "slug literals outside the SLUGS tuple: " + str(offenders))

    def test_the_shape_regex_actually_matches_the_slugs(self):
        """Fixture integrity: a shape check that matched nothing would be
        vacuous."""
        for slug in codex_gate.SLUGS:
            self.assertRegex(slug, self.SLUG_SHAPE)


# --------------------------------------------------------------------------- #
# Purity — the import set is EXACTLY {json, sys}
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob", "re",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(CODEX_GATE_PY, "r", encoding="utf-8") as fh:
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
            "codex_gate.py imports outside the allowed set: "
            + str(imported - self.ALLOWED),
        )

    def test_no_forbidden_module_imported(self):
        for name in self._imported():
            self.assertNotIn(name, self.FORBIDDEN_NAMES)

    def test_no_forbidden_calls_or_attributes(self):
        banned_call_names = {"eval", "exec", "compile", "__import__", "open"}
        banned_attr_roots = {"os", "subprocess", "pathlib", "shutil", "glob"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned_call_names,
                                 "forbidden call: " + node.func.id)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                self.assertNotIn(node.value.id, banned_attr_roots,
                                 "forbidden attribute access on: "
                                 + node.value.id)


if __name__ == "__main__":
    unittest.main()
