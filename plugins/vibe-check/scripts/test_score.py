"""Pinning unit tests for score.py — the deterministic-core extraction (Phase 16).

This is the FIRST test suite in the plugin. It pins the CURRENT scoring.md +
review.md behavior byte-for-byte so the extraction is provably equivalent
(Phase 17 hardens; Phase 16 only freezes the current outputs).

Run from repo root:
    python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'
Or from this dir:
    cd plugins/vibe-check/scripts && python3 -m unittest

NOTE: importing `os`/`ast`/`subprocess` in THIS test file is fine — the import
ban is on score.py exclusively. The AST test below enforces that ban on score.py.
"""

import ast
import os
import subprocess
import sys
import unittest

# Make `import score` resolve when unittest discovery runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import score  # noqa: E402  (sibling module under test)

SCORE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "score.py")


# --------------------------------------------------------------------------- #
# Test fixtures / helpers
# --------------------------------------------------------------------------- #
def make_finding(**overrides):
    """A minimal valid finding (agent-output-schema shape) with sane defaults.

    Defaults are chosen so the bare finding scores predictably:
    agent_confidence=100, severity=critical (+0), no diff/silenced/intent/etc.
    """
    f = {
        "id": "x-001",
        "file": "src/a.py",
        "line": 10,
        "title": "some bug",
        "category": "bug",
        "cwe": None,
        "severity": "critical",
        "agent_confidence": 100,
        "in_diff": False,
        "intent_doc_match": None,
        "problem": "p",
        "current_code": "  x = 1",
        "fix_hint": None,
        "why_it_matters": "w",
        "silenced_marker_nearby": False,
        "agent": "bugs",
    }
    f.update(overrides)
    return f


def score_of(finding, *, in_diff=False, silenced=False, cross_confirmed=False,
             persisted=False):
    """Convenience wrapper around score.compute_score with keyword overrides."""
    return score.compute_score(
        finding,
        in_diff=in_diff,
        silenced=silenced,
        cross_confirmed=cross_confirmed,
        persisted=persisted,
    )


# --------------------------------------------------------------------------- #
# band_for — every band boundary (D-07)
# --------------------------------------------------------------------------- #
class TestBandBoundaries(unittest.TestCase):
    def test_95_is_critical(self):
        self.assertEqual(score.band_for(95), "critical")

    def test_100_is_critical(self):
        self.assertEqual(score.band_for(100), "critical")

    def test_94_is_warning(self):
        self.assertEqual(score.band_for(94), "warning")

    def test_80_is_warning(self):
        self.assertEqual(score.band_for(80), "warning")

    def test_79_is_medium(self):
        self.assertEqual(score.band_for(79), "medium")

    def test_70_is_medium(self):
        self.assertEqual(score.band_for(70), "medium")

    def test_69_is_below_both_thresholds(self):
        # <70 is below both /review (80) and /deep-review (70) thresholds —
        # never a rendered band.
        self.assertIsNone(score.band_for(69))

    def test_0_is_below(self):
        self.assertIsNone(score.band_for(0))


# --------------------------------------------------------------------------- #
# Severity weight branches (scoring.md:21-26) — applied LAST before clamp
# --------------------------------------------------------------------------- #
class TestSeverityWeight(unittest.TestCase):
    # Base finding: agent_confidence=80, no other modifiers, so the result
    # isolates the severity weight: 80 + weight.
    def _base(self, severity):
        return make_finding(agent_confidence=80, severity=severity)

    def test_critical_plus_zero(self):
        self.assertEqual(score_of(self._base("critical")), 80)

    def test_high_minus_three(self):
        self.assertEqual(score_of(self._base("high")), 77)

    def test_medium_minus_eight(self):
        self.assertEqual(score_of(self._base("medium")), 72)

    def test_low_minus_twenty(self):
        self.assertEqual(score_of(self._base("low")), 60)

    def test_unset_severity_fallback_minus_eight(self):
        # severity missing entirely -> -8 medium-equivalent fallback.
        f = make_finding(agent_confidence=80)
        del f["severity"]
        self.assertEqual(score_of(f), 72)

    def test_unrecognized_severity_fallback_minus_eight(self):
        self.assertEqual(score_of(self._base("bogus")), 72)


# --------------------------------------------------------------------------- #
# Each additive modifier in isolation (scoring.md:11-19)
# --------------------------------------------------------------------------- #
class TestAdditiveModifiers(unittest.TestCase):
    def _base(self):
        # agent_confidence=50, severity critical (+0) so the delta is the modifier.
        return make_finding(agent_confidence=50, severity="critical")

    def test_in_diff_plus_twenty(self):
        self.assertEqual(score_of(self._base(), in_diff=True), 70)

    def test_silenced_minus_fifty(self):
        # 50 - 50 = 0 (pre-clamp 0, not <0, so it survives as 0).
        self.assertEqual(score_of(self._base(), silenced=True), 0)

    def test_compliance_agent_plus_twenty(self):
        f = self._base()
        f["agent"] = "compliance"
        self.assertEqual(score_of(f), 70)

    def test_non_compliance_agent_no_bonus(self):
        f = self._base()
        f["agent"] = "security"
        self.assertEqual(score_of(f), 50)

    def test_cross_confirmed_plus_ten(self):
        self.assertEqual(score_of(self._base(), cross_confirmed=True), 60)

    def test_persisted_plus_fifteen(self):
        self.assertEqual(score_of(self._base(), persisted=True), 65)

    def test_two_agent_finding_scores_exactly_ten_over_one_agent(self):
        base = score_of(self._base(), cross_confirmed=False)
        confirmed = score_of(self._base(), cross_confirmed=True)
        self.assertEqual(confirmed - base, 10)


# --------------------------------------------------------------------------- #
# Intent-doc MUTUAL EXCLUSION (D-12) — elif, strictly greater-than
# --------------------------------------------------------------------------- #
class TestIntentDocMutualExclusion(unittest.TestCase):
    def _base(self, confidence):
        return make_finding(
            agent_confidence=100,
            severity="critical",
            intent_doc_match={"doc": "PLAN.md", "section": "s", "quote": "q",
                              "confidence": confidence},
        )

    def test_strong_match_minus_100_only_not_130(self):
        # confidence 0.95 > 0.9 -> -100 ONLY (never -100 then -30 stacked).
        # 100 - 100 = 0 (survives at floor).
        self.assertEqual(score_of(self._base(0.95)), 0)

    def test_partial_match_minus_30(self):
        # confidence 0.8 -> -30. 100 - 30 = 70.
        self.assertEqual(score_of(self._base(0.8)), 70)

    def test_exactly_0_7_no_penalty_strictly_greater(self):
        # 0.7 is NOT > 0.7 -> no penalty. 100 - 0 = 100.
        self.assertEqual(score_of(self._base(0.7)), 100)

    def test_just_above_0_7_gets_penalty(self):
        self.assertEqual(score_of(self._base(0.71)), 70)

    def test_exactly_0_9_only_partial_penalty(self):
        # 0.9 is NOT > 0.9, but IS > 0.7 -> -30 (partial), not -100.
        self.assertEqual(score_of(self._base(0.9)), 70)

    def test_null_intent_doc_no_penalty(self):
        f = make_finding(agent_confidence=100, severity="critical",
                         intent_doc_match=None)
        self.assertEqual(score_of(f), 100)

    def test_malformed_intent_doc_treated_as_no_match(self):
        # Defensive (V5/T-16-02): a malformed intent_doc_match (missing
        # confidence) must be treated as no match, not crash.
        f = make_finding(agent_confidence=100, severity="critical",
                         intent_doc_match={"doc": "PLAN.md"})
        self.assertEqual(score_of(f), 100)


# --------------------------------------------------------------------------- #
# Clamp [0,100] at both ends (scoring.md:29)
# --------------------------------------------------------------------------- #
class TestClamp(unittest.TestCase):
    def test_over_100_clamps_to_100(self):
        # agent_confidence=100, +20 in_diff, +20 compliance, +10 cross,
        # +15 persisted = 165 pre-clamp -> clamp 100.
        f = make_finding(agent_confidence=100, severity="critical",
                         agent="compliance")
        self.assertEqual(
            score_of(f, in_diff=True, cross_confirmed=True, persisted=True),
            100,
        )

    def test_floor_survivor_clamps_to_0_not_dropped(self):
        # pre-clamp exactly 0 must survive as 0 (only pre-clamp <0 drops).
        f = make_finding(agent_confidence=50, severity="critical")
        self.assertEqual(score_of(f, silenced=True), 0)


# --------------------------------------------------------------------------- #
# DROP rule (D-14) — pre-clamp < 0 ⇒ DROP entirely (not clamp-to-0)
# --------------------------------------------------------------------------- #
class TestDropRule(unittest.TestCase):
    def test_pre_clamp_negative_returns_drop_signal(self):
        # agent_confidence=40, silenced -50, severity medium -8 = -18 pre-clamp.
        # < 0 -> DROP (compute_score returns None, the drop signal).
        f = make_finding(agent_confidence=40, severity="medium")
        self.assertIsNone(score_of(f, silenced=True))

    def test_drop_via_run_absent_from_findings_present_in_filtered(self):
        # The dropped finding must be ABSENT from output findings[] and PRESENT
        # in filtered[] (NOT clamped-to-0-and-emitted).
        f = make_finding(id="drop-1", agent_confidence=40, severity="medium",
                         silenced_marker_nearby=True,
                         source_window=["x", "# noqa", "y"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)
        ids = [g["id"] for g in result["findings"]]
        self.assertNotIn("drop-1", ids)
        # It is recorded in filtered[] with a reason.
        filtered_titles = [x for x in result["filtered"]]
        self.assertTrue(len(filtered_titles) >= 1)


# --------------------------------------------------------------------------- #
# Per-command threshold filter (scoring.md:57-64) — one parameter, not 2 paths
# --------------------------------------------------------------------------- #
class TestThresholds(unittest.TestCase):
    def _envelope(self, command, agent_confidence):
        f = make_finding(id="t-1", agent_confidence=agent_confidence,
                         severity="critical", line=10,
                         source_window=["a", "b", "c", "d", "e"])
        return {
            "command": command,
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {},
            "carryforward": [],
            "findings": [f],
        }

    def test_review_filters_below_80(self):
        # score 79 < 80 -> filtered as sub-threshold under /review.
        result = score.run(self._envelope("review", 79))
        self.assertEqual([g["id"] for g in result["findings"]], [])
        self.assertTrue(
            any(x.get("reason") == "sub-threshold" for x in result["filtered"])
        )

    def test_review_keeps_80(self):
        result = score.run(self._envelope("review", 80))
        self.assertEqual([g["id"] for g in result["findings"]], ["t-1"])

    def test_deep_review_keeps_70(self):
        # score 70 >= 70 -> survives under /deep-review.
        result = score.run(self._envelope("deep-review", 70))
        self.assertEqual([g["id"] for g in result["findings"]], ["t-1"])

    def test_deep_review_filters_below_70(self):
        result = score.run(self._envelope("deep-review", 69))
        self.assertEqual([g["id"] for g in result["findings"]], [])
        self.assertTrue(
            any(x.get("reason") == "sub-threshold" for x in result["filtered"])
        )

    def test_deep_review_keeps_79_review_filters_79(self):
        # 79 is Medium band: surfaced only by /deep-review, filtered by /review.
        self.assertEqual(
            [g["id"] for g in score.run(self._envelope("deep-review", 79))["findings"]],
            ["t-1"],
        )
        self.assertEqual(
            [g["id"] for g in score.run(self._envelope("review", 79))["findings"]],
            [],
        )


# --------------------------------------------------------------------------- #
# silenced_nearby — ±2 window (D-13), the 5 canonical markers (review.md:685)
# --------------------------------------------------------------------------- #
class TestSilencedNearby(unittest.TestCase):
    MARKERS = ["eslint-disable", "# noqa", "// nolint", "@SuppressWarnings",
               "#[allow("]

    def test_each_canonical_marker_detected(self):
        for marker in self.MARKERS:
            with self.subTest(marker=marker):
                window = ["plain", "code " + marker + " here", "more"]
                self.assertTrue(score.silenced_nearby(window))

    def test_no_marker_returns_false(self):
        self.assertFalse(score.silenced_nearby(["a", "b", "c", "d", "e"]))

    def test_marker_at_window_edge_minus2(self):
        # Inclusive [L-2 .. L+2]: a marker at the far edge still counts.
        window = ["eslint-disable", "b", "c", "d", "e"]
        self.assertTrue(score.silenced_nearby(window))

    def test_marker_at_window_edge_plus2(self):
        window = ["a", "b", "c", "d", "x // nolint"]
        self.assertTrue(score.silenced_nearby(window))

    def test_empty_window_false(self):
        self.assertFalse(score.silenced_nearby([]))


# --------------------------------------------------------------------------- #
# carry_forward_status (review.md:672-678, D-11 strip both sides)
# --------------------------------------------------------------------------- #
class TestCarryForwardStatus(unittest.TestCase):
    def test_null_canonical_is_fixed_since_last(self):
        f = make_finding(current_code="  return q")
        self.assertEqual(score.carry_forward_status(f, None), "fixed-since-last")

    def test_matching_first_line_is_persisted(self):
        # First line of current_code stripped == canonical stripped -> persisted.
        f = make_finding(current_code="  return q\n  more")
        self.assertEqual(score.carry_forward_status(f, "return q"), "persisted")

    def test_whitespace_drift_both_sides_stripped_still_persisted(self):
        # D-11: strip BOTH sides — leading/trailing whitespace drift is NOT a
        # false "fixed".
        f = make_finding(current_code="    return q   ")
        self.assertEqual(score.carry_forward_status(f, "  return q  "), "persisted")

    def test_content_changed_is_needs_recheck(self):
        f = make_finding(current_code="  return q")
        self.assertEqual(
            score.carry_forward_status(f, "return DIFFERENT"), "needs-recheck"
        )


# --------------------------------------------------------------------------- #
# cross_confirm_group (review.md:689, D-13 line±2, D-15 substring title)
# --------------------------------------------------------------------------- #
class TestCrossConfirmGroup(unittest.TestCase):
    def test_same_file_within_2_lines_substring_title_grouped(self):
        a = make_finding(id="a", file="src/a.py", line=10,
                         title="SQL injection", agent="security")
        b = make_finding(id="b", file="src/a.py", line=12,
                         title="SQL injection in query builder", agent="bugs")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]["attribution"]), ["bugs", "security"])

    def test_case_insensitive_substring(self):
        a = make_finding(id="a", file="src/a.py", line=10, title="Null deref",
                         agent="bugs")
        b = make_finding(id="b", file="src/a.py", line=11,
                         title="possible NULL DEREF on user", agent="security")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["attribution"]), 2)

    def test_different_file_not_grouped(self):
        a = make_finding(id="a", file="src/a.py", line=10, title="bug")
        b = make_finding(id="b", file="src/b.py", line=10, title="bug")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_line_distance_over_2_not_grouped(self):
        a = make_finding(id="a", file="src/a.py", line=10, title="bug")
        b = make_finding(id="b", file="src/a.py", line=13, title="bug")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_no_title_overlap_not_grouped(self):
        a = make_finding(id="a", file="src/a.py", line=10, title="SQL injection")
        b = make_finding(id="b", file="src/a.py", line=11, title="memory leak")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_single_finding_single_group_one_agent_attribution(self):
        a = make_finding(id="a", file="src/a.py", line=10, title="bug",
                         agent="bugs")
        groups = score.cross_confirm_group([a])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["attribution"], ["bugs"])


# --------------------------------------------------------------------------- #
# GOLDEN sha256 stable_hash (MANDATORY — T-16-01)
# --------------------------------------------------------------------------- #
class TestStableHashGolden(unittest.TestCase):
    def test_golden_digest_frozen(self):
        # Frozen literal — any separator/encoding/field-order drift fails here.
        # Recipe: sha256((file + "\x00" + canonical_line_content + "\x00" + title))
        # Separator is NUL (M1): the old "\n" separator was forgeable (collision),
        # so the digest was re-pinned when the separator changed.
        self.assertEqual(
            score.stable_hash("a.py", "  x=1", "title"),
            "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124",
        )

    def test_hash_is_deterministic(self):
        h1 = score.stable_hash("f.py", "code", "t")
        h2 = score.stable_hash("f.py", "code", "t")
        self.assertEqual(h1, h2)

    def test_field_order_matters(self):
        # Swapping file and title must change the digest (proves order is fixed).
        self.assertNotEqual(
            score.stable_hash("a.py", "  x=1", "title"),
            score.stable_hash("title", "  x=1", "a.py"),
        )


# --------------------------------------------------------------------------- #
# AST import-set assertion (finding #5 / T-16-03) — enforce the import ban
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "hashlib", "re", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "difflib", "eval", "exec", "compile", "__import__",
                       "open"}

    def _tree(self):
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_subset_of_allowed(self):
        tree = self._tree()
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "score.py imports outside {json,hashlib,re,sys}: "
            + str(imported - self.ALLOWED),
        )

    def test_no_forbidden_module_imported(self):
        tree = self._tree()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    self.assertNotIn(top, self.FORBIDDEN_NAMES)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    self.assertNotIn(top, self.FORBIDDEN_NAMES)

    def test_no_forbidden_calls_or_attributes(self):
        # Walk Call/Name/Attribute nodes for os.*, subprocess, open(, eval(,
        # exec(, compile(, __import__. (AST ignores string/comment tokens.)
        tree = self._tree()
        banned_call_names = {"eval", "exec", "compile", "__import__", "open"}
        banned_attr_roots = {"os", "subprocess", "pathlib", "shutil", "glob"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name):
                    self.assertNotIn(fn.id, banned_call_names,
                                     "forbidden call: " + fn.id)
            if isinstance(node, ast.Attribute):
                # Catch os.path / os.listdir / subprocess.run etc.
                val = node.value
                if isinstance(val, ast.Name):
                    self.assertNotIn(val.id, banned_attr_roots,
                                     "forbidden attribute access on: " + val.id)


# --------------------------------------------------------------------------- #
# MALFORMED-STDIN fail-closed (finding #1 / T-16-02)
# --------------------------------------------------------------------------- #
class TestFailClosed(unittest.TestCase):
    def test_invalid_json_stdin_exits_nonzero(self):
        # Pipe garbage to `python3 score.py`; the process MUST exit non-zero so
        # the orchestrator's fail-closed gate (16-02) can fail the review closed.
        proc = subprocess.run(
            [sys.executable, SCORE_PY],
            input=b"not json",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        proc = subprocess.run(
            [sys.executable, SCORE_PY],
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(proc.returncode, 0)


# --------------------------------------------------------------------------- #
# run(envelope) end-to-end
# --------------------------------------------------------------------------- #
class TestRunEndToEnd(unittest.TestCase):
    def _envelope(self, **over):
        base = {
            "command": "review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [
                make_finding(id="keep-1", agent_confidence=85, severity="critical",
                             line=10, source_window=["a", "b", "c", "d", "e"]),
            ],
        }
        base.update(over)
        return base

    def test_sentinel_stamped(self):
        result = score.run(self._envelope())
        self.assertTrue(result["scored_by_script"])

    def test_survivor_carries_scored_fields(self):
        result = score.run(self._envelope())
        self.assertEqual(len(result["findings"]), 1)
        g = result["findings"][0]
        # in_diff recomputed (line 10 in [8,14]) -> 85 + 20 = 105 -> clamp 100.
        self.assertEqual(g["orchestrator_score"], 100)
        self.assertEqual(g["band"], "critical")
        self.assertIn("stable_hash", g)
        self.assertIn("attribution", g)

    def test_input_fields_preserved_verbatim(self):
        result = score.run(self._envelope())
        g = result["findings"][0]
        for field in ("id", "file", "line", "title", "category", "severity",
                      "problem", "current_code", "why_it_matters"):
            self.assertIn(field, g)

    def test_in_diff_recomputed_overrides_agent_claim(self):
        # Agent self-reports in_diff True, but line 99 is NOT in [8,14]; the
        # script overrides and the +20 does not apply (hard rule #4).
        f = make_finding(id="ood", agent_confidence=85, severity="critical",
                         line=99, in_diff=True,
                         source_window=["a", "b", "c", "d", "e"])
        result = score.run(self._envelope(findings=[f]))
        # 85, no +20 -> 85 still passes /review (>=80). Score must be 85 not 105.
        self.assertEqual(result["findings"][0]["orchestrator_score"], 85)

    def test_fixed_since_last_excluded_from_findings(self):
        # A carryforward finding whose file:line is gone -> fixed-since-last,
        # excluded from reported findings, surfaced in fixed_since_last[].
        cf = make_finding(id="cf-gone", file="src/a.py", line=10,
                          title="old bug", current_code="  gone",
                          canonical_line_content=None)
        result = score.run(self._envelope(carryforward=[cf], findings=[]))
        self.assertNotIn("cf-gone", [g["id"] for g in result["findings"]])
        self.assertTrue(len(result["fixed_since_last"]) >= 1)

    def test_persisted_carryforward_gets_plus_15(self):
        # A carryforward finding whose canonical content still matches ->
        # persisted, +15, included.
        cf = make_finding(id="cf-keep", file="src/a.py", line=10,
                          title="still here", agent_confidence=60,
                          severity="critical", current_code="  return q",
                          canonical_line_content="return q",
                          source_window=["a", "b", "c", "d", "e"])
        # line 10 in [8,14] -> in_diff +20; +15 persisted; conf 60 = 95 -> critical.
        result = score.run(self._envelope(carryforward=[cf], findings=[]))
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("cf-keep", survivors)
        self.assertEqual(survivors["cf-keep"]["status"], "persisted")
        self.assertEqual(survivors["cf-keep"]["orchestrator_score"], 95)


# --------------------------------------------------------------------------- #
# C1 — float agent_confidence must NOT be silently zeroed (deep-review C1)
# --------------------------------------------------------------------------- #
class TestFloatConfidence(unittest.TestCase):
    def test_float_confidence_scores_same_as_int(self):
        # 85.0 (float, as JSON from LLM agents routinely carries) must score
        # identically to 85 (int) — not get coerced to 0 by an isinstance int check.
        f_float = make_finding(agent_confidence=85.0, severity="critical")
        f_int = make_finding(agent_confidence=85, severity="critical")
        self.assertEqual(score_of(f_float), score_of(f_int))
        self.assertEqual(score_of(f_float), 85)

    def test_fractional_float_truncated_to_int(self):
        # A fractional float is accepted (not zeroed); truncated via int().
        f = make_finding(agent_confidence=85.9, severity="critical")
        self.assertEqual(score_of(f), 85)

    def test_bool_confidence_rejected_to_zero(self):
        # bool is an int subclass; True must NOT count as confidence 1 — it is
        # rejected to 0 (then severity critical +0 -> 0).
        f_true = make_finding(agent_confidence=True, severity="critical")
        self.assertEqual(score_of(f_true), 0)
        f_false = make_finding(agent_confidence=False, severity="critical")
        self.assertEqual(score_of(f_false), 0)


# --------------------------------------------------------------------------- #
# W1 — stable_hash is None-safe; a null title must not halt the whole review
# --------------------------------------------------------------------------- #
class TestStableHashNoneSafe(unittest.TestCase):
    def test_none_arg_equals_empty_string_arg(self):
        # A None field hashes identically to "" for that field (no crash).
        self.assertEqual(
            score.stable_hash(None, "  x=1", "title"),
            score.stable_hash("", "  x=1", "title"),
        )
        self.assertEqual(
            score.stable_hash("a.py", None, "title"),
            score.stable_hash("a.py", "", "title"),
        )
        self.assertEqual(
            score.stable_hash("a.py", "  x=1", None),
            score.stable_hash("a.py", "  x=1", ""),
        )

    def test_all_none_does_not_raise(self):
        # Returns a valid hex digest rather than raising TypeError.
        h = score.stable_hash(None, None, None)
        self.assertEqual(len(h), 64)

    def test_null_title_finding_flows_through_run_without_raising(self):
        # A malformed-but-parseable finding with title=null must NOT crash run()
        # (which would propagate non-zero and trip the orchestrator fail-closed
        # halt on the entire review).
        f = make_finding(id="null-title", title=None, agent_confidence=85,
                         severity="critical", line=10,
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])
        # It survived scoring and carries a stable_hash computed with title="".
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("null-title", survivors)
        self.assertIn("stable_hash", survivors["null-title"])


# --------------------------------------------------------------------------- #
# M1 — NUL separator: new golden pinned + the newline collision is gone
# --------------------------------------------------------------------------- #
class TestStableHashSeparatorCollision(unittest.TestCase):
    def test_new_golden_digest_pinned(self):
        self.assertEqual(
            score.stable_hash("a.py", "  x=1", "title"),
            "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124",
        )

    def test_newline_separator_collision_no_longer_occurs(self):
        # Under the old "\n" separator these two inputs collided:
        #   ('a.py','x','y\nz')  ==  ('a.py','x\ny','z')
        # With the NUL separator they must differ (NUL cannot appear in the fields).
        self.assertNotEqual(
            score.stable_hash("a.py", "x", "y\nz"),
            score.stable_hash("a.py", "x\ny", "z"),
        )


# --------------------------------------------------------------------------- #
# W2 — explicit line:null must not crash grouping or the diff/range checks
# --------------------------------------------------------------------------- #
class TestNullLineDefensive(unittest.TestCase):
    def test_null_line_finding_flows_through_run_without_raising(self):
        # A file-level finding legitimately carries line=null; run() must not
        # crash on abs(None - 0) or `1 <= None <= n`.
        f = make_finding(id="file-level", line=None, agent_confidence=85,
                         severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])

    def test_two_null_line_findings_do_not_group_on_line(self):
        # Two null-line findings in the same file with matching titles must NOT
        # group on line-distance (a null line is not a usable ±2 coordinate).
        a = make_finding(id="a", file="src/a.py", line=None, title="bug",
                         agent="bugs")
        b = make_finding(id="b", file="src/a.py", line=None, title="bug",
                         agent="security")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_line_in_ranges_null_line_is_out_of_range(self):
        self.assertFalse(score._line_in_ranges(None, [[1, 100]]))

    def test_all_mode_null_line_not_in_reviewed_set(self):
        # In --all mode with a known file line total, a null-line finding fails
        # the 1<=line<=N bound (out of range) instead of raising.
        f = make_finding(id="al", file="src/a.py", line=None,
                         agent_confidence=85, severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": True,
            "pass_number": 1,
            "reviewed_union": ["src/a.py"],
            "file_line_totals": {"src/a.py": 50},
            "changed_line_ranges": {},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertNotIn("al", [g["id"] for g in result["findings"]])


if __name__ == "__main__":
    unittest.main()
