"""Tests for calibrate.py — the B-REWEIGHT derivation (D-15).

Every lock carries a demonstrated failure: the D-04/D-06 boundary is proven to
raise on a planted violation and to pass on the untouched manifest, lower-only
and thin-agent identity are proven on synthetic tables, the rounding rule is
pinned on an exact half, and the real-archive tests fail (never skip) when the
archives are missing.
"""

import ast
import copy
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import calibrate  # noqa: E402  (sibling module under test)
import replay  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CALIBRATE_PY = os.path.join(HERE, "calibrate.py")

# The verbatim output of `calibrate.py counts` / `derive` over the committed
# archives; CALIBRATION-v2.10.md carries the same numbers.
EXPECTED_COUNTS = {
    "architecture": {"tp": 6, "fp": 6, "n": 12},
    "bugs": {"tp": 22, "fp": 13, "n": 35},
    "codex-adversarial": {"tp": 18, "fp": 4, "n": 22},
    "compliance": {"tp": 7, "fp": 0, "n": 7},
    "framework-fastapi": {"tp": 2, "fp": 0, "n": 2},
    "impact": {"tp": 24, "fp": 26, "n": 50},
    "language-typescript": {"tp": 2, "fp": 0, "n": 2},
    "security": {"tp": 15, "fp": 2, "n": 17},
}
EXPECTED_POOL = (96, 147)
EXPECTED_OFFSETS = {"architecture": -6, "bugs": -2, "impact": -12}
EXPECTED_CALIBRATION_CATCH_RUNS = 21
EXPECTED_QUIET_RUNS = 24


def _row(tp, fp):
    return {"tp": tp, "fp": fp, "n": tp + fp}


_ARCHIVE_CACHE = {}


def _archives():
    if not _ARCHIVE_CACHE:
        _ARCHIVE_CACHE["manifest"] = replay.load_manifest()
        _ARCHIVE_CACHE["runs"] = replay.iter_runs()
    return _ARCHIVE_CACHE["manifest"], _ARCHIVE_CACHE["runs"]


def _run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = calibrate.run(argv)
    return code, out.getvalue(), err.getvalue()


class TestMethodConstants(unittest.TestCase):
    def test_alpha(self):
        self.assertEqual(calibrate.ALPHA, 20)

    def test_min_labeled(self):
        self.assertEqual(calibrate.MIN_LABELED, 5)

    def test_calibration_archives_are_claude5_only(self):
        self.assertEqual(calibrate.CALIBRATION_ARCHIVES, ("runs-v2.10", "runs-v2.10-phase40"))
        self.assertNotIn("runs", calibrate.CALIBRATION_ARCHIVES)

    def test_firing_bands(self):
        self.assertEqual(calibrate.FIRING_BANDS, ("critical", "warning"))


class TestCounts(unittest.TestCase):
    def setUp(self):
        self.manifest, self.runs = _archives()
        self.assertNotEqual(len(self.runs), 0,
                            "no archived runs found — calibration must fail, not skip")

    def test_labeled_run_denominators(self):
        cal = [k for k, e in self.manifest["catch_runs"].items()
               if e.get("calibration") is True]
        self.assertEqual(len(cal), EXPECTED_CALIBRATION_CATCH_RUNS)
        quiet = self.manifest["quiet_runs"]["headline"] + self.manifest["quiet_runs"]["phase40"]
        self.assertEqual(len(quiet), EXPECTED_QUIET_RUNS)

    def test_counts_equal_the_recorded_table(self):
        self.assertEqual(calibrate.counts(self.manifest, self.runs), EXPECTED_COUNTS)

    def test_pooled_precision_is_the_table_sum(self):
        table = calibrate.counts(self.manifest, self.runs)
        num, den = calibrate.pooled_precision(table)
        self.assertEqual(den, sum(r["tp"] + r["fp"] for r in table.values()))
        self.assertEqual((num, den), EXPECTED_POOL)

    def test_every_counted_agent_is_a_str_and_none_malformed(self):
        table = calibrate.counts(self.manifest, self.runs)
        self.assertTrue(all(isinstance(a, str) for a in table))
        self.assertNotIn(calibrate.MALFORMED_AGENT, table)

    def test_non_firing_quiet_survivor_is_not_an_fp(self):
        manifest = copy.deepcopy(self.manifest)
        runs = copy.deepcopy(self.runs)
        path = manifest["quiet_runs"]["headline"][0]
        run = next(r for r in runs if r["rel_path"] == path)
        before = calibrate.counts(manifest, runs)
        run["state"]["passes"][-1]["findings"].append(
            {"agent": "planted-agent", "band": "medium"})
        self.assertEqual(calibrate.counts(manifest, runs), before)
        run["state"]["passes"][-1]["findings"].append(
            {"agent": "planted-agent", "band": "warning"})
        self.assertEqual(calibrate.counts(manifest, runs)["planted-agent"],
                         {"tp": 0, "fp": 1, "n": 1})


class TestDeriveProperties(unittest.TestCase):
    def test_real_offsets(self):
        manifest, runs = _archives()
        table = calibrate.counts(manifest, runs)
        offsets = calibrate.derive(manifest, runs)
        self.assertEqual(offsets, EXPECTED_OFFSETS)
        for agent, off in offsets.items():
            self.assertIsInstance(off, int)
            self.assertLess(off, 0)
            self.assertGreaterEqual(table[agent]["n"], calibrate.MIN_LABELED)

    def test_lower_only_agent_above_pool_is_absent(self):
        table = {"high": _row(40, 0), "low": _row(10, 40)}
        offsets = calibrate.offsets_from_table(table)
        self.assertNotIn("high", offsets)
        self.assertIn("low", offsets)
        self.assertLess(offsets["low"], 0)

    def test_thin_agent_is_identity_below_min_labeled(self):
        table = {"pool": _row(50, 50), "thin": _row(0, 4)}
        self.assertNotIn("thin", calibrate.offsets_from_table(table))
        table["thin"] = _row(0, 5)
        self.assertIn("thin", calibrate.offsets_from_table(table))

    def test_empty_table_is_identity(self):
        self.assertEqual(calibrate.offsets_from_table({}), {})

    def test_derive_reads_the_alpha_constant(self):
        # Module-constant swap: a weaker prior moves the offsets, so the
        # constant is the one the derivation uses (not a shadow literal).
        manifest, runs = _archives()
        saved = calibrate.ALPHA
        try:
            calibrate.ALPHA = 5
            swapped = calibrate.derive(manifest, runs)
        finally:
            calibrate.ALPHA = saved
        self.assertNotEqual(swapped, EXPECTED_OFFSETS)
        self.assertEqual(calibrate.derive(manifest, runs), EXPECTED_OFFSETS)

    def test_derive_reads_the_min_labeled_constant(self):
        table = {"pool": _row(50, 50), "thin": _row(0, 5)}
        saved = calibrate.MIN_LABELED
        try:
            calibrate.MIN_LABELED = 6
            self.assertNotIn("thin", calibrate.offsets_from_table(table))
        finally:
            calibrate.MIN_LABELED = saved
        self.assertIn("thin", calibrate.offsets_from_table(table))


class TestRoundingRule(unittest.TestCase):
    def test_exact_halves_round_half_to_even(self):
        # Pool = 200/400 = 1/2. "a": p_hat = (9 + 10)/40 = 19/40, so
        # 100*(p_hat - p_pool) = -5/2 exactly -> -2. "c": p_hat = (83 + 10)/200,
        # 100*(p_hat - p_pool) = -7/2 exactly -> -4. Half-to-even, not half-down
        # and not half-away-from-zero.
        table = {"a": _row(9, 11), "b": _row(11, 9), "c": _row(83, 97), "d": _row(97, 83)}
        self.assertEqual(calibrate.offsets_from_table(table), {"a": -2, "c": -4})


class TestBoundaryAsserted(unittest.TestCase):
    def test_boundary_violations_raise_and_the_untouched_manifest_passes(self):
        manifest, runs = _archives()

        m1 = copy.deepcopy(manifest)
        v29_quiet = m1["quiet_runs"]["v29_informational"][0]
        self.assertTrue(v29_quiet.startswith("runs/"))
        m1["quiet_runs"]["headline"].append(v29_quiet)
        with self.assertRaises(calibrate.CalibrationError):
            calibrate.counts(m1, runs)

        m2 = copy.deepcopy(manifest)
        m2["quiet_runs"]["headline"].append(m2["excluded_runs"]["should-quiet-7"][0])
        with self.assertRaises(calibrate.CalibrationError):
            calibrate.counts(m2, runs)

        m3 = copy.deepcopy(manifest)
        v29_catch = next(k for k, e in m3["catch_runs"].items() if e["archive"] == "runs")
        m3["catch_runs"][v29_catch]["calibration"] = True
        with self.assertRaises(calibrate.CalibrationError):
            calibrate.counts(m3, runs)

        # Non-vacuous: the same call on the untouched manifest succeeds.
        self.assertEqual(calibrate.counts(copy.deepcopy(manifest), runs), EXPECTED_COUNTS)

    def test_quiet_run_missing_from_archive_raises(self):
        manifest, runs = _archives()
        m = copy.deepcopy(manifest)
        m["quiet_runs"]["headline"].append("runs-v2.10/should-quiet-1/run-99")
        with self.assertRaises(calibrate.CalibrationError):
            calibrate.counts(m, runs)


class TestCli(unittest.TestCase):
    def test_counts_output(self):
        code, out, _err = _run_cli(["counts"])
        self.assertEqual(code, 0)
        self.assertIn("pooled precision = ΣTP/Σ(TP+FP) = %d/%d" % EXPECTED_POOL, out)
        self.assertIn("ALPHA=20 MIN_LABELED=5", out)
        self.assertIn("| impact | 24 | 26 | 50 | yes |", out)

    def test_derive_output_is_sorted_json(self):
        code, out, _err = _run_cli(["derive"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), EXPECTED_OFFSETS)
        self.assertEqual(out, json.dumps(EXPECTED_OFFSETS, sort_keys=True) + "\n")

    def test_usage_errors_exit_2(self):
        self.assertEqual(_run_cli([])[0], 2)
        self.assertEqual(_run_cli(["bogus"])[0], 2)
        self.assertEqual(_run_cli(["derive", "--check"])[0], 2)

    def test_check_compares_against_score(self):
        import score
        saved = getattr(score, "AGENT_CONFIDENCE_OFFSET", None)
        had = hasattr(score, "AGENT_CONFIDENCE_OFFSET")
        try:
            score.AGENT_CONFIDENCE_OFFSET = dict(EXPECTED_OFFSETS)
            self.assertEqual(_run_cli(["--check"])[0], 0)
            score.AGENT_CONFIDENCE_OFFSET = dict(EXPECTED_OFFSETS, impact=-13)
            self.assertEqual(_run_cli(["--check"])[0], 1)
            del score.AGENT_CONFIDENCE_OFFSET
            code, out, _err = _run_cli(["--check"])
            self.assertEqual(code, 1)
            self.assertIn("score.py has no AGENT_CONFIDENCE_OFFSET", out)
        finally:
            if had:
                score.AGENT_CONFIDENCE_OFFSET = saved
            elif hasattr(score, "AGENT_CONFIDENCE_OFFSET"):
                del score.AGENT_CONFIDENCE_OFFSET


class TestEmbeddedEqualsDerived(unittest.TestCase):
    """score.AGENT_CONFIDENCE_OFFSET is the derivation, not a hand-edited constant (T3).

    Fails — never skips — when the archives are missing: a lock that skips on a
    fresh clone would let a hand-edited literal through unnoticed.
    """

    def _live(self):
        manifest, runs = _archives()
        if not runs:
            self.fail("archives missing — this lock must never skip")
        return manifest, runs

    def test_embedded_offsets_equal_derivation(self):
        import score
        manifest, runs = self._live()
        self.assertEqual(score.AGENT_CONFIDENCE_OFFSET,
                         calibrate.derive(manifest, runs))

    def test_perturbed_label_breaks_equality(self):
        # Mutation proof: flip ONE axis:true -> false on a survivor of the keyed
        # agent with the fewest TPs (impact when keyed), in a calibration run. The
        # derivation must move off the embedded literal; the untouched manifest
        # must still equal it (non-vacuous).
        import score
        manifest, runs = self._live()
        embedded = score.AGENT_CONFIDENCE_OFFSET
        self.assertTrue(embedded, "no keyed agent to perturb")
        table = calibrate.counts(manifest, runs)
        target = ("impact" if "impact" in embedded
                  else min(embedded, key=lambda a: table[a]["tp"]))

        mutated = copy.deepcopy(manifest)
        flipped = False
        for _path, entry in sorted(mutated["catch_runs"].items()):
            if not isinstance(entry, dict) or entry.get("calibration") is not True:
                continue
            for s in entry.get("survivors_at_site") or []:
                if (isinstance(s, dict) and s.get("agent") == target
                        and s.get("axis") is True):
                    s["axis"] = False
                    flipped = True
                    break
            if flipped:
                break
        self.assertTrue(flipped, "no %s axis:true survivor to flip" % target)

        self.assertNotEqual(calibrate.derive(mutated, runs), embedded)
        self.assertEqual(calibrate.derive(copy.deepcopy(manifest), runs), embedded)

    def test_check_cli_exit_zero(self):
        self._live()
        self.assertEqual(_run_cli(["--check"])[0], 0)


class TestMethodRecord(unittest.TestCase):
    """CALIBRATION-v2.10.md carries the verbatim `counts` and `derive` output."""

    DOC = os.path.join(replay.REPO_ROOT, "docs", "design", "b3-ground-truth",
                       "CALIBRATION-v2.10.md")

    def _fenced_after(self, heading):
        with open(self.DOC, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index(heading)
        body = text[text.index("```\n", start) + 4:]
        return body[:body.index("```\n")]

    def test_counts_block_is_verbatim(self):
        _code, out, _err = _run_cli(["counts"])
        self.assertEqual(self._fenced_after("## Labeled counts"), out)

    def test_derive_block_is_verbatim(self):
        _code, out, _err = _run_cli(["derive"])
        self.assertEqual(self._fenced_after("## Derived offsets"), out)


class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "fractions", "json", "os", "sys", "replay", "score"}

    def _tree(self):
        with open(CALIBRATE_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_imports_are_exactly_the_allowed_set(self):
        found = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
        self.assertEqual(found, self.ALLOWED)
        self.assertNotIn("subprocess", found)

    def test_no_live_state_path_literal(self):
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertNotIn(".turingmind", node.value)


if __name__ == "__main__":
    unittest.main()
